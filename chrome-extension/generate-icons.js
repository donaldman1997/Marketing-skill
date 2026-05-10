// Run with: node generate-icons.js
// Generates placeholder icons using the 'canvas' npm package.
// In production replace with proper branded icons.
const { createCanvas } = require("canvas");
const fs = require("fs");
const path = require("path");

[16, 48, 128].forEach((size) => {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext("2d");

  // Background
  const grad = ctx.createLinearGradient(0, 0, size, size);
  grad.addColorStop(0, "#4F46E5");
  grad.addColorStop(1, "#7C3AED");
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.roundRect(0, 0, size, size, size * 0.2);
  ctx.fill();

  // Letter M
  ctx.fillStyle = "#fff";
  ctx.font = `bold ${Math.round(size * 0.55)}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("M", size / 2, size / 2 + size * 0.03);

  const buf = canvas.toBuffer("image/png");
  fs.writeFileSync(path.join(__dirname, "icons", `icon${size}.png`), buf);
  console.log(`icon${size}.png written`);
});
