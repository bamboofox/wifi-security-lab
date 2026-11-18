# BambooFox Wi-Fi Security 練習

瀏覽器練習需要 Python 3、支援 TLS 1.3 的 Python SSL 模組，以及 PATH 中的 `openssl`。也可直接用 Wireshark 開啟隨附封包。

```sh
python3 lab.py
```

若 macOS 系統內建的 `python3` 缺少 TLS 1.3，請使用新版 Python。Apple Silicon 上既有的 Homebrew Python 通常可用 `/opt/homebrew/bin/python3 lab.py` 啟動。

瀏覽器開 [127.0.0.1:8765](http://127.0.0.1:8765/)。若連接埠已被佔用，可加上 `--port 8766`。用 Ctrl+C 結束服務。

## 1. 比較 HTTP 與 TLS

先預測傳輸途中哪一種會出現 `fox-student`，再按「比較 HTTP 與 TLS」。

- 左欄的樣本資料固定，畫面沒有可填寫或提交的憑證。
- 右欄的 HTTP 顯示本機 socket pair 收到的固定請求位元組。TLS 欄位顯示兩個本機 TLS 端點在記憶體中實際交換的應用資料記錄，並檢查完整記錄是否包含固定明文。
- 比較 TLS 記錄和伺服器解密後的結果。用戶端第一次僅在自己的 TLS context 信任暫存測試憑證，第二次使用空的信任集合，檢查會收到什麼錯誤。
- 網頁本身透過本機 HTTP 顯示；TLS 實驗由 Python 執行。憑證與私鑰在實驗後刪除，瀏覽器和系統的憑證設定無須調整。

## 2. 比較圖片完整性

開啟「相簿」。按「模擬替換」或從裝置選擇 PNG、JPEG 或 WebP，三張圖片會同時換成相同的圖。按「還原原圖」切回阿波羅 11 號的照片。自選圖留在瀏覽器內。

這一頁是瀏覽器內的回應結果模擬。討論時把三個位置標出來：原始檔案、傳輸中的內容、瀏覽器顯示的內容。再說明經過驗證的 TLS 如何保護傳輸完整性。

## 3. Wireshark 封包練習

[操作步驟與預期結果](wireshark/README.md) · [本機實測封包檔](wireshark/http-tls-loopback.pcap)

## 檢查

```sh
python3 -c 'from lab import evidence; x = evidence(); assert x["httpBodyVisible"] and not x["tlsBodyVisible"] and x["tlsVersion"] == "TLSv1.3" and x["rejection"]; print("HTTP, TLS 1.3 and certificate verification passed")'
```
