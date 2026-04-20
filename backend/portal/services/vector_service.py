# Vector Service - 向量数据库服务
# 使用 PostgreSQL + pgvector 实现 RAG

import os
import uuid
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import execute_values
import anthropic

from app.core.config import get_settings, get_uploads_dir

# 向量数据库配置 - 从 Settings 获取
def _get_vector_db_url():
    return get_settings().vector_db_url

# 向量维度（Claude embedding 使用 1024 维）
VECTOR_DIMENSION = 1024

# 分块配置
CHUNK_SIZE = 500  # 每块字符数
CHUNK_OVERLAP = 50  # 块之间重叠字符数


@dataclass
class DocumentChunk:
    """文档分块"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class VectorService:
    """向量数据库服务"""

    def __init__(self):
        self.settings = get_settings()
        client_kwargs = self.settings.get_anthropic_client_kwargs()
        self.client = anthropic.Anthropic(**client_kwargs)
        self._db_initialized = False

    def _ensure_db(self):
        """延迟初始化数据库（首次使用时）"""
        if not self._db_initialized:
            try:
                self._init_db()
                self._db_initialized = True
            except Exception as e:
                print(f"[VectorService] Database initialization failed: {e}")
                raise

    def _get_connection(self, skip_init=False):
        """获取数据库连接"""
        if not skip_init:
            self._ensure_db()
        return psycopg2.connect(_get_vector_db_url())

    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection(skip_init=True) as conn:
            with conn.cursor() as cur:
                # 启用 pgvector 扩展
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

                # 创建文档表
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS document_embeddings (
                        id VARCHAR(50) PRIMARY KEY,
                        file_id VARCHAR(50) NOT NULL,
                        agent_id VARCHAR(50),
                        user_id VARCHAR(50) NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        content_hash VARCHAR(64) NOT NULL,
                        metadata JSONB DEFAULT '{}',
                        embedding vector(1024),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                        CONSTRAINT unique_file_chunk UNIQUE (file_id, chunk_index)
                    )
                """)

                # 创建索引
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_doc_emb_agent_id
                    ON document_embeddings(agent_id)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_doc_emb_user_id
                    ON document_embeddings(user_id)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_doc_emb_file_id
                    ON document_embeddings(file_id)
                """)

                # 创建向量索引（使用 IVFFlat 加速搜索）
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_doc_emb_vector
                    ON document_embeddings
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)

                conn.commit()
        print("[VectorService] Database initialized")

    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示"""
        # 使用 Claude 的 embedding API
        # 注意：如果 Claude 不支持 embedding，需要使用其他服务（如 OpenAI 或本地模型）
        try:
            # 尝试使用 Anthropic embedding（如果可用）
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": f"Generate embedding for: {text[:100]}"}]
            )
            # 这里需要实际的 embedding API
            # 暂时使用简单的哈希模拟
            return self._simple_embedding(text)
        except Exception:
            return self._simple_embedding(text)

    def _simple_embedding(self, text: str) -> List[float]:
        """简单的文本向量化（用于测试）"""
        # 使用哈希生成确定性向量（生产环境应使用真实 embedding 模型）
        import hashlib
        hash_bytes = hashlib.sha512(text.encode()).digest()
        # 扩展到 1024 维
        embedding = []
        for i in range(VECTOR_DIMENSION):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
        return embedding

    def _chunk_text(self, text: str) -> List[str]:
        """将文本分块"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - CHUNK_OVERLAP
        return chunks

    def _extract_text(self, file_path: str) -> str:
        """从文件中提取文本"""
        path = Path(file_path)
        suffix = path.suffix.lower()

        try:
            if suffix in ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml']:
                return path.read_text(encoding='utf-8')

            elif suffix == '.pdf':
                try:
                    import PyPDF2
                    with open(path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        return text
                except ImportError:
                    print("[VectorService] PyPDF2 not installed, skipping PDF")
                    return ""

            elif suffix in ['.xlsx', '.xls']:
                try:
                    import pandas as pd
                    # 读取所有 sheet
                    xlsx = pd.ExcelFile(path)
                    all_text = []

                    for sheet_name in xlsx.sheet_names:
                        df = pd.read_excel(xlsx, sheet_name=sheet_name)
                        if df.empty:
                            continue

                        all_text.append(f"=== Sheet: {sheet_name} ===")

                        # 按行转换，保留结构
                        columns = df.columns.tolist()
                        for idx, row in df.iterrows():
                            row_text = []
                            for col in columns:
                                val = row[col]
                                if pd.notna(val):
                                    row_text.append(f"{col}: {val}")
                            if row_text:
                                all_text.append("; ".join(row_text))

                    return "\n".join(all_text)
                except ImportError:
                    print("[VectorService] pandas not installed, skipping Excel")
                    return ""

            elif suffix == '.csv':
                try:
                    import pandas as pd
                    df = pd.read_csv(path)
                    return df.to_string()
                except ImportError:
                    return path.read_text(encoding='utf-8')

            elif suffix == '.docx':
                try:
                    from docx import Document
                    doc = Document(path)
                    return "\n".join([para.text for para in doc.paragraphs])
                except ImportError:
                    print("[VectorService] python-docx not installed, skipping DOCX")
                    return ""

            else:
                # 尝试作为文本读取
                try:
                    return path.read_text(encoding='utf-8')
                except:
                    return ""
        except Exception as e:
            print(f"[VectorService] Error extracting text from {file_path}: {e}")
            return ""

    async def index_file(
        self,
        file_id: str,
        file_path: str,
        user_id: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        索引文件到向量数据库

        Args:
            file_id: 文件ID（DataNote ID）
            file_path: 文件路径
            user_id: 用户ID
            agent_id: Agent ID（用于数据隔离）
            metadata: 额外元数据

        Returns:
            索引的分块数量
        """
        # 提取文本
        text = self._extract_text(file_path)
        if not text.strip():
            print(f"[VectorService] No text extracted from {file_path}")
            return 0

        # 分块
        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        # 删除旧的索引
        await self.delete_file_index(file_id)

        # 生成向量并存储
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                rows = []
                for i, chunk_text in enumerate(chunks):
                    chunk_id = str(uuid.uuid4())
                    content_hash = hashlib.md5(chunk_text.encode()).hexdigest()
                    embedding = self._get_embedding(chunk_text)

                    rows.append((
                        chunk_id,
                        file_id,
                        agent_id,
                        user_id,
                        i,
                        chunk_text,
                        content_hash,
                        json.dumps(metadata or {}, ensure_ascii=False),  # 转成 JSON 字符串
                        embedding
                    ))

                # 批量插入
                execute_values(
                    cur,
                    """
                    INSERT INTO document_embeddings
                    (id, file_id, agent_id, user_id, chunk_index, content, content_hash, metadata, embedding)
                    VALUES %s
                    """,
                    rows,
                    template="(%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector)"
                )
                conn.commit()

        print(f"[VectorService] Indexed {len(chunks)} chunks for file {file_id}")
        return len(chunks)

    async def delete_file_index(self, file_id: str):
        """删除文件的向量索引"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM document_embeddings WHERE file_id = %s",
                    (file_id,)
                )
                deleted = cur.rowcount
                conn.commit()
        if deleted:
            print(f"[VectorService] Deleted {deleted} chunks for file {file_id}")

    async def search(
        self,
        query: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        向量相似度搜索

        Args:
            query: 查询文本
            agent_id: Agent ID（用于数据隔离）
            user_id: 用户ID
            top_k: 返回结果数量
            threshold: 相似度阈值

        Returns:
            相关文档列表
        """
        # 获取查询向量
        query_embedding = self._get_embedding(query)
        print(f"[VectorService] search: query={query[:50]}..., agent_id={agent_id}, user_id={user_id}, top_k={top_k}, threshold={threshold}")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # 构建查询条件
                # 注意：agent_id 和 user_id 都是可选的，只有提供时才过滤
                conditions = []
                params = []

                if agent_id:
                    conditions.append("agent_id = %s")
                    params.append(agent_id)

                # user_id 改为可选过滤（不强制要求匹配）
                # 如果需要严格的用户隔离，可以取消下面的注释
                # if user_id:
                #     conditions.append("user_id = %s")
                #     params.append(user_id)

                where_clause = " AND ".join(conditions) if conditions else "1=1"
                print(f"[VectorService] search: WHERE {where_clause}, params={params}")

                # 先检查总数
                cur.execute(f"SELECT COUNT(*) FROM document_embeddings WHERE {where_clause}", params)
                total_count = cur.fetchone()[0]
                print(f"[VectorService] search: total matching records = {total_count}")

                # 向量相似度搜索
                cur.execute(f"""
                    SELECT
                        id, file_id, content, metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM document_embeddings
                    WHERE {where_clause}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, [str(query_embedding)] + params + [str(query_embedding), top_k])

                results = []
                for row in cur.fetchall():
                    similarity = row[4]
                    print(f"[VectorService] search: found chunk, similarity={similarity:.4f}, content={row[2][:30]}...")
                    if similarity >= threshold:
                        results.append({
                            "id": row[0],
                            "file_id": row[1],
                            "content": row[2],
                            "metadata": row[3],
                            "similarity": similarity
                        })

                print(f"[VectorService] search: returning {len(results)} results (threshold={threshold})")

        return results

    async def get_context_for_chat(
        self,
        query: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        max_context_length: int = 4000
    ) -> str:
        """
        获取对话的 RAG 上下文

        Args:
            query: 用户查询
            agent_id: Agent ID
            user_id: 用户ID
            max_context_length: 最大上下文长度

        Returns:
            格式化的上下文文本
        """
        # 使用较低的阈值，因为当前使用的是简单哈希向量（非语义向量）
        # 真正部署时应使用真正的 embedding 模型（如 OpenAI、Claude 或本地模型）
        results = await self.search(
            query=query,
            agent_id=agent_id,
            user_id=user_id,
            top_k=20,  # 返回更多结果
            threshold=0.0  # 暂时不过滤，返回所有结果
        )
        print(f"[VectorService] get_context_for_chat: query={query[:30]}..., agent_id={agent_id}, user_id={user_id}, results={len(results)}")

        if not results:
            return ""

        context_parts = []
        total_length = 0

        # 按文件分组
        file_groups = {}
        for result in results:
            file_id = result.get("file_id", "unknown")
            metadata = result.get("metadata", {})
            file_name = metadata.get("name", "未知文件") if isinstance(metadata, dict) else "未知文件"

            if file_id not in file_groups:
                file_groups[file_id] = {
                    "name": file_name,
                    "chunks": []
                }
            file_groups[file_id]["chunks"].append(result)

        # 格式化输出
        for file_id, file_data in file_groups.items():
            file_name = file_data["name"]
            chunks = file_data["chunks"]

            # 文件标题
            file_section = f"### 来源文件: {file_name}\n\n"

            # 添加数据行
            for i, chunk in enumerate(chunks[:10], 1):  # 每个文件最多10条
                content = chunk["content"]
                similarity = chunk.get("similarity", 0)

                if total_length + len(content) > max_context_length:
                    break

                # 格式化单条数据
                file_section += f"**数据 {i}** (相似度: {similarity:.1%})\n"
                file_section += f"```\n{content}\n```\n\n"
                total_length += len(content) + 50

            context_parts.append(file_section)

            if total_length > max_context_length:
                break

        if not context_parts:
            return ""

        return "\n".join(context_parts)

    async def get_file_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """获取向量库统计信息"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if agent_id:
                    cur.execute("""
                        SELECT
                            COUNT(DISTINCT file_id) as file_count,
                            COUNT(*) as chunk_count
                        FROM document_embeddings
                        WHERE agent_id = %s
                    """, (agent_id,))
                else:
                    cur.execute("""
                        SELECT
                            COUNT(DISTINCT file_id) as file_count,
                            COUNT(*) as chunk_count
                        FROM document_embeddings
                    """)

                row = cur.fetchone()
                return {
                    "file_count": row[0],
                    "chunk_count": row[1]
                }


# 全局实例
_vector_service: Optional[VectorService] = None


def get_vector_service() -> Optional[VectorService]:
    """获取向量服务实例，如果向量数据库未启用则返回 None"""
    global _vector_service

    # 检查是否启用向量数据库
    from app.core.config import get_settings
    settings = get_settings()
    if not settings.vector_db_enabled:
        return None

    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
