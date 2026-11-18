# Wireshark 練習：HTTP、HTTPS 與憑證驗證

[下載封包檔](https://github.com/BambooFox/wifi-security-lab/raw/refs/heads/main/wireshark/http-tls-loopback.pcap)。用 Wireshark 開啟即可開始。本檔有 51 個封包、三條 TCP 連線，全部由同一台 Mac 上的測試程式經 `127.0.0.1` 產生。

| Wireshark 顯示篩選器 | 先找什麼 | 觀察重點 |
| --- | --- | --- |
| `tcp.stream == 0` | 第 6 幀，`POST /lesson` | 可重組出完整 HTTP 請求與回應 |
| `tcp.stream == 1` | 第 19、21、25 幀 | Client Hello、Server Hello、加密記錄 |
| `tcp.stream == 2` | 第 45、47、49 幀 | 開始 TLS 握手，第 49 幀回報 `Unknown CA` |

每次在頂端的顯示篩選器輸入上表其中一列，再按 Enter。

## 1. 讀 HTTP 明文

篩選 `tcp.stream == 0`，選第 6 幀，按右鍵選 **Follow → TCP Stream**。能讀到 `POST /lesson`、Content-Type、請求內容和 `200 OK`。記下這個欄位。

```text
alias=fox-student&lesson=wifi-security
```

請求標頭和內容跨兩個 TCP 封包。Follow TCP Stream 會依序重組。關閉 Follow 視窗後，可以用下一條篩選器取代目前的篩選器。

## 2. 找出 HTTPS 的 TLS 版本

篩選 `tcp.stream == 1`。第 19 幀是 Client Hello，展開 TLS 的 **Extension: server_name** 可以讀到 `localhost`。第 21 幀是 Server Hello，看 **Extension: supported_versions** 選到 `TLS 1.3 (0x0304)`。Client Hello 的 Protocol 欄可能寫 TLSv1.2，這是相容用的傳統標示。判斷協商結果時以 Server Hello 的擴充欄位為準。

第 25 幀起可看到 Application Data。再用 Follow → TCP Stream 並切到 **Hex Dump** 看同一條連線。應用請求使用與第一條連線相同的固定資料，用戶端實測回傳 `200 OK`，封包內容中讀不到 `fox-student`。TLS 1.3 有些加密的握手記錄也使用 Application Data 外層類型。

## 3. 找到憑證驗證失敗的證據

篩選 `tcp.stream == 2`，或輸入 `tls.alert_message.desc == 48` 直接找第 49 幀。這一份擷取檔的用戶端發出 **Fatal / Unknown CA**，請求在 HTTP 資料送出前就已因驗證失敗而中止。兩條 TLS 連線用了同一張暫存測試憑證。第二條 TCP 連線的用戶端明確信任它，第三條的用戶端沒有把它載入自己的信任設定。

## 4. 重錄自己的範例（選做）

1. 在 Wireshark 選系統的 loopback 介面（macOS 是 `lo0`），填入下列**擷取篩選器**，再開始擷取。

   ```text
   ip and src host 127.0.0.1 and dst host 127.0.0.1 and (tcp port 18080 or tcp port 18443)
   ```

2. 在專案根目錄執行 `python3 -B wireshark/make_traffic.py`，需要支援 TLS 1.3 的 Python 與 `openssl`。程式的兩個監聽端點只綁在 `127.0.0.1`，跑完即關閉。應看到兩次 `200 OK` 和一次 `certificate verification rejected`。
3. 停止擷取，再用上面的顯示篩選器比對。自行重錄的幀號和封包數可能不同。若 Wireshark 沒自動辨認協定，對代表性封包用 **Analyze → Decode As…**，將 TCP port `18080` 指定為 HTTP、`18443` 指定為 TLS。

參考 [Wireshark Follow Stream](https://www.wireshark.org/docs/wsug_html_chunked/ChAdvFollowStreamSection.html) 與 [Loopback Capture](https://wiki.wireshark.org/CaptureSetup/Loopback)。
