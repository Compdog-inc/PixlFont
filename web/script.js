const words = [
	"PIXEL UI",
	"COLOR GLYPHS",
	"MODERN BLOCKS",
	"SCREEN BLEND",
	"WEB FONT READY"
];

const typedWordEl = document.getElementById("typedWord");
const blendTextSharpEl = document.getElementById("blendTextSharp");
const blendTextBlurEl = document.getElementById("blendTextBlur");

const previewTextInputEl = document.getElementById("globalPreviewText");
const previewSizeInputEl = document.getElementById("globalSize");
const sizeValueEl = document.getElementById("sizeValue");
const formatCheckboxEls = Array.from(document.querySelectorAll(".format-toggle"));
const variantLiveTextEls = Array.from(document.querySelectorAll(".variant-live-text"));
const snippetCodeEls = Array.from(document.querySelectorAll(".snippet-code"));
const copyButtons = Array.from(document.querySelectorAll(".copy-btn"));
const releaseRepoPlaceholder = "Compdog-inc/PixlFont";

let wordIndex = 0;
let charIndex = 0;
let isDeleting = false;

function setDisplayText(value) {
	const displayValue = value || "\u00A0";
	typedWordEl.textContent = displayValue;
	blendTextSharpEl.textContent = displayValue;
	blendTextBlurEl.textContent = displayValue;
}

function runTypewriter() {
	const currentWord = words[wordIndex];

	if (isDeleting) {
		charIndex -= 1;
	} else {
		charIndex += 1;
	}

	charIndex = Math.max(0, Math.min(charIndex, currentWord.length));
	setDisplayText(currentWord.slice(0, charIndex));

	let delay = isDeleting ? 55 : 95;

	if (!isDeleting && charIndex === currentWord.length) {
		isDeleting = true;
		delay = 1100;
	} else if (isDeleting && charIndex === 0) {
		isDeleting = false;
		wordIndex = (wordIndex + 1) % words.length;
		delay = 280;
	}

	window.setTimeout(runTypewriter, delay);
}

function applyVariantText(value) {
	const normalized = value && value.length ? value : "\u00A0";
	for (const textEl of variantLiveTextEls) {
		textEl.textContent = normalized;
	}
}

function applyVariantSize(px) {
	document.documentElement.style.setProperty("--variant-size", `${px}px`);
	if (sizeValueEl) {
		sizeValueEl.textContent = `${px}px`;
	}
}

function getSelectedFormats() {
	const checkedValues = formatCheckboxEls
		.filter((checkboxEl) => checkboxEl.checked)
		.map((checkboxEl) => checkboxEl.value);

	if (checkedValues.length > 0) {
		return checkedValues;
	}

	const woff2Toggle = formatCheckboxEls.find((checkboxEl) => checkboxEl.value === "woff2");
	if (woff2Toggle) {
		woff2Toggle.checked = true;
	}

	return ["woff2"];
}

function buildSnippetCode(family, fileName, selectedFormats) {
	const baseName = fileName.replace(/\.woff2$/i, "");
	const formatMeta = {
		woff2: {
			url: `https://github.com/${releaseRepoPlaceholder}/releases/latest/download/${baseName}.woff2`,
			label: "woff2"
		},
		woff: {
			url: `https://github.com/${releaseRepoPlaceholder}/releases/latest/download/${baseName}.woff`,
			label: "woff"
		},
		ttf: {
			url: `https://github.com/${releaseRepoPlaceholder}/releases/latest/download/${baseName}.ttf`,
			label: "truetype"
		}
	};

	const srcLines = selectedFormats.map((format, index) => {
		const meta = formatMeta[format];
		if (!meta) {
			return null;
		}
		const suffix = index < selectedFormats.length - 1 ? "," : ";";
		return `    url(\"${meta.url}\") format(\"${meta.label}\")${suffix}`;
	}).filter(Boolean);

	return [
		"@font-face {",
		`  font-family: \"${family}\";`,
		"  src:",
		...srcLines,
		"  font-weight: 400;",
		"  font-style: normal;",
		"  font-display: swap;",
		"}"
	].join("\n");
}

function renderAllSnippets() {
	const selectedFormats = getSelectedFormats();
	for (const codeEl of snippetCodeEls) {
		const family = codeEl.dataset.family;
		const fileName = codeEl.dataset.file;
		if (!family || !fileName) {
			continue;
		}
		codeEl.textContent = buildSnippetCode(family, fileName, selectedFormats);
	}
}

async function copySnippetFromButton(buttonEl) {
	const targetId = buttonEl.dataset.copyTarget;
	if (!targetId) {
		return;
	}

	const sourceEl = document.getElementById(targetId);
	if (!sourceEl) {
		return;
	}

	const snippetText = sourceEl.textContent || "";
	if (!snippetText) {
		return;
	}

	const originalLabel = buttonEl.textContent;
	try {
		await navigator.clipboard.writeText(snippetText);
		buttonEl.textContent = "Copied";
	} catch (error) {
		buttonEl.textContent = "Failed";
	}

	window.setTimeout(() => {
		buttonEl.textContent = originalLabel;
	}, 1200);
}

if (typedWordEl && blendTextSharpEl && blendTextBlurEl) {
	setDisplayText(words[0]);
	window.setTimeout(runTypewriter, 650);
}

if (previewTextInputEl) {
	applyVariantText(previewTextInputEl.value);
	previewTextInputEl.addEventListener("input", () => {
		applyVariantText(previewTextInputEl.value);
	});
}

if (previewSizeInputEl) {
	applyVariantSize(previewSizeInputEl.value);
	previewSizeInputEl.addEventListener("input", () => {
		applyVariantSize(previewSizeInputEl.value);
	});
}

renderAllSnippets();

for (const checkboxEl of formatCheckboxEls) {
	checkboxEl.addEventListener("change", renderAllSnippets);
}

for (const buttonEl of copyButtons) {
	buttonEl.addEventListener("click", () => {
		copySnippetFromButton(buttonEl);
	});
}
