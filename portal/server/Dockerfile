FROM python:3.11-slim

WORKDIR /app

# Install Chinese fonts for PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    fonts-noto-cjk \
    fontconfig \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure matplotlib to use Chinese fonts globally
RUN mkdir -p /root/.config/matplotlib && \
    echo "font.family: WenQuanYi Micro Hei" > /root/.config/matplotlib/matplotlibrc && \
    echo "axes.unicode_minus: False" >> /root/.config/matplotlib/matplotlibrc

# Set environment for Chinese locale
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 120

# Copy source
COPY . .

# Create directories
RUN mkdir -p skills_storage outputs uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
