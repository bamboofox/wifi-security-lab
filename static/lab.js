const compare = document.querySelector("#compare");
const status = document.querySelector("#status");

if (compare) {
	compare.addEventListener("click", async () => {
		compare.disabled = true;
		try {
			const response = await fetch("evidence.json");
			if (!response.ok) throw new Error("Evidence unavailable");
			const sample = await response.json();
			document.querySelector("#plain").textContent = sample.http;
			document.querySelector("#encrypted").textContent = sample.tlsHex + " …";
			document.querySelector("#http-state").textContent = sample.httpBodyVisible ? "可讀取樣本" : "找不到樣本";
			document.querySelector("#tls-state").textContent = sample.tlsBodyVisible ? "可讀取樣本" : `${sample.tlsVersion} · 掃描 ${sample.tlsLength} B 未見明文`;
			document.querySelector("#verification").textContent = `伺服器解密後取得 ${sample.serverReceived}。未信任憑證的用戶端：${sample.rejection}。`;
			document.querySelector("#prompt").hidden = true;
			document.querySelector("#results").hidden = false;
			status.textContent = "已顯示本機 TLS 實測";
		} catch {
			status.textContent = "讀取失敗。請確認已從本機 lab.py 開啟練習。";
		} finally {
			compare.disabled = false;
		}
	});
}

const toggle = document.querySelector("#toggle");

if (toggle) {
	const fileInput = document.querySelector("#replacement");
	const originals = Array.from(document.querySelectorAll(".gallery img"), image => ({
		image,
		src: image.getAttribute("src"),
		alt: image.alt
	}));
	const sample = "images/two.svg";
	let replacement;
	let active = false;

	function render() {
		for (const original of originals) {
			original.image.src = active ? (replacement ?? sample) : original.src;
			original.image.alt = active ? "重播後的替換圖" : original.alt;
		}
		toggle.textContent = active ? "返回原始圖片" : "重播圖片替換";
		toggle.setAttribute("aria-pressed", String(active));
		status.textContent = active ? "目前顯示替換後的圖片" : "目前顯示原始圖片";
	}

	toggle.addEventListener("click", () => {
		active = !active;
		render();
	});

	fileInput.addEventListener("change", async () => {
		const file = fileInput.files[0];
		if (!file) return;
		const candidate = URL.createObjectURL(file);
		const test = new Image();
		test.src = candidate;
		try {
			await test.decode();
		} catch {
			URL.revokeObjectURL(candidate);
			if (fileInput.files[0] === file) status.textContent = "無法讀取圖片，請選擇 PNG、JPEG 或 WebP。";
			return;
		}
		if (fileInput.files[0] !== file) {
			URL.revokeObjectURL(candidate);
			return;
		}
		if (replacement) URL.revokeObjectURL(replacement);
		replacement = candidate;
		active = true;
		render();
	});
}
