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

## 3. 用 Wireshark 觀察自己的登入

1. 在自己電腦上啟動練習，開 [登入頁](http://127.0.0.1:8765/login.html)。使用其他連接埠時，把下列網址與篩選器的 `8765` 換成終端機印出的數字。
2. 在 Wireshark 選擇本機的 loopback 介面。macOS 顯示為 `lo0` 或 **Loopback**。開始前可在**擷取篩選器**輸入 `host 127.0.0.1 and tcp port 8765`。
3. 開始擷取後，在瀏覽器按「使用示範帳號登入」。確認跳到「已登入」，接著按「登出」，然後停止擷取。
4. 在 Wireshark 的**顯示篩選器**輸入 `http.request.method == "POST" and http.request.uri == "/login"`。如果沒出現資料，在這份擷取檔中對連接埠 `8765` 的 TCP 封包選 **Analyze → Decode As…**，將該連接埠指定為 **HTTP**，再套用篩選器。
5. 選取找到的請求，按右鍵選 **Follow → TCP Stream**。找出下列固定資料及同一條連線內的 `303 See Other`、`Location: /account.html`、`Set-Cookie: foxframe_demo=…`。

```text
POST /login HTTP/1.1
…
alias=fox-student&lesson=wifi-security
```

關掉 Follow 視窗，再把顯示篩選器換成 `http.cookie contains "foxframe_demo"`，觀察瀏覽器在後續請求送回 Cookie。以 `http.request.uri == "/logout"` 找登出請求，並觀察回應如何清除 Cookie。每次登入都會建立短效示範工作階段，登出會立即移除。帳號與課程代號都是公開測試值，頁面只會送出這組固定資料。

## 4. HTTP / HTTPS 對照封包

[操作步驟與預期結果](wireshark/README.md) · [本機實測封包檔](wireshark/http-tls-loopback.pcap)

## 檢查

```sh
python3 -c 'from lab import evidence; x = evidence(); assert x["httpBodyVisible"] and not x["tlsBodyVisible"] and x["tlsVersion"] == "TLSv1.3" and x["rejection"]; print("HTTP, TLS 1.3 and certificate verification passed")'
```
