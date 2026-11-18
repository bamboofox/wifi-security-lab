const compare = document.querySelector("#compare");
const status = document.querySelector("#status");

if (compare) {
	const results = document.querySelector("#results");
	compare.addEventListener("click", async () => {
		if (!results.hidden) {
			results.hidden = true;
			compare.textContent = "比較 HTTP 與 TLS";
			compare.setAttribute("aria-expanded", "false");
			return;
		}
		compare.disabled = true;
		status.textContent = "";
		try {
			const response = await fetch("evidence.json");
			if (!response.ok) throw new Error("Evidence unavailable");
			const sample = await response.json();
			document.querySelector("#plain").textContent = sample.http;
			document.querySelector("#encrypted").textContent = sample.tlsHex + " …";
			document.querySelector("#http-state").textContent = sample.httpBodyVisible ? "可讀取明文" : "未找到樣本";
			document.querySelector("#tls-state").textContent = sample.tlsBodyVisible ? "可讀取明文" : `${sample.tlsVersion} · ${sample.tlsLength} B`;
			document.querySelector("#verification").textContent = `伺服器解密後：${sample.serverReceived}。憑證未受信任：${sample.rejection}。`;
			results.hidden = false;
			compare.textContent = "收合傳輸內容";
			compare.setAttribute("aria-expanded", "true");
		} catch {
			status.textContent = "無法讀取本機實測結果。";
		} finally {
			compare.disabled = false;
		}
	});
}

const toggle = document.querySelector("#toggle");

if (toggle) {
	const gallery = document.querySelector("#gallery");
	const fileInput = document.querySelector("#replacement");
	const originals = Array.from(gallery.querySelectorAll("img"), image => ({
		image,
		src: image.getAttribute("src"),
		alt: image.alt
	}));
	let replacement;
	let active = false;

	function render() {
		for (const { image, src, alt } of originals) {
			image.src = active ? (replacement ?? originals[1].src) : src;
			image.alt = active ? (replacement ? "自選替換圖" : originals[1].alt) : alt;
		}
		gallery.toggleAttribute("data-replaced", active);
		toggle.textContent = active ? "還原原圖" : "模擬替換";
		status.textContent = "";
	}

	toggle.addEventListener("click", () => {
		active = !active;
		render();
	});

	document.querySelector("#pick").addEventListener("click", () => fileInput.click());
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
			if (fileInput.files[0] === file) status.textContent = "無法讀取這張圖片。";
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
