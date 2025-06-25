# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 2
timeout = 30
preload_app = True  # 预加载应用，减少内存占用