## Sing-Box 订阅配置生成

仅测试 ss vless

**请求订阅会缓存 8 小时，存储在 cache 目录。如有相同请求的订阅转换（公益站）谨慎使用**

## 运行

```bash
# pip3 install -r ./requirements.txt
# python3 main.py
```

### Docker

```bash
docker run -dit --name singsub -p 5000:5000 --restart always antonhub/singsub:latest
```

## 生成

```bash
curl -s -H 'Content-Type: application/json; charset=utf-8' -X POST http://127.0.0.1:5000/api/v1/sing-box \
     --data '{"urls": ["https://example.com/link/uRgy3MPET9rwR6id?sub=1", "https://example.com/link/34LHYPGzu5a4rha6?sub=1"]}' > config.json
```

可选参数：

- 落地出口 `relay_outs`：base64 编码的节点，多个换行。
- 版本 `version`：使用不同的模板，默认提供了两份 1.7 和 1.8 的配置。你可以自定义配置以 `xxx-config.json` 作为文件名，传参 `{"version": "xxx"}` 即可调用

完整请求：

```bash
curl -s -H 'Content-Type: application/json; charset=utf-8' -X POST http://127.0.0.1:5000/api/v1/sing-box \
     --data '{"urls": ["https://example.com/link/uRgy3MPET9rwR6id?sub=1", "https://example.com/link/34LHYPGzu5a4rha6?sub=1"], "relay_outs": "6L-Z5LuW5aaI55qE5Y-q5piv56S65L6L77yM5LiN5piv6IqC54K5", "version": "1.8"}' > config.json
```

## 感谢

- [Sing-Box Documentation](https://sing-box.sagernet.org/configuration/)
- [Toperlock/sing-box-subscribe](https://github.com/Toperlock/sing-box-subscribe)