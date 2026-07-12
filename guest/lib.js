'use strict';

const convertHexStringToRgbaValues = (str) => {
  const decimalValue = parseInt(str, 16);
  const paletteWidth = 47;
  let val = decimalValue * paletteWidth;
  const color = {r: 0, g: 0, b: 0};
  if (val > 255*2) {
    color.b = Math.round(val - 255*2);
    color.r = color.g = 255;
  } else if (val > 255) {
    color.g = Math.round(val - 255);
    color.r = 255;
  } else {
    color.r = Math.round(val);
  }
  return color;
};

const convertHexStringToRgba = (str) => {
  const {r, g, b} = convertHexStringToRgbaValues(str);
  return `rgba(${r}, ${g}, ${b}, 1)`;
};

const clearCanvas = (ctx_) => {
  ctx_.beginPath();
  ctx_.rect(0, 0, ctx_.canvas.width, ctx_.canvas.height);
  ctx_.fillStyle = '#000000';
  ctx_.fill();
  ctx_.closePath();
};

const getNumSquaresPerPage = (ctx, sqWidth, withMeta=true) => {
  const w = ctx.canvas.width;
  const h = ctx.canvas.height;
  const sq = parseInt(sqWidth);
  const metaData = withMeta ? w * sq : 0;
  return (w*h - metaData) / sq / sq;
};

const calcNumPages = (numHalfBytes, numSquaresPerPage) => {
  return Math.ceil(numHalfBytes / numSquaresPerPage);
};

const updateNumPages = () => {
  const elem = document.getElementById("pageTracker");
  elem.innerHTML = `<h1>page ${offset+1}/${numPages}</h1>`;

  const kittenElem = document.getElementById("kittenImg");
  if (kittenElem) {
    if (hexArray.length > 0) {
      kittenElem.src = (offset + 1) % 2 === 0 ? "img1.jpeg" : "img0.jpeg";
      kittenElem.style.display = "block";
    } else {
      kittenElem.style.display = "none";
    }
  }
};

const handleFiles = (files) => {
  if (!files.length) {
    fileList.innerHTML = "<p>No files selected!</p>";
  } else {
    fileList.innerHTML = "";
    const list = document.createElement("ul");
    fileList.appendChild(list);
    for (let i = 0; i < files.length; i++) {
      const li_fname = document.createElement("li");
      list.appendChild(li_fname);
      const info = document.createElement("span");
      info.innerHTML = files[i].name;
      li_fname.appendChild(info);
      const li_size = document.createElement("li");
      list.appendChild(li_size);
      const sz = document.createElement("span");
      sz.innerHTML = files[i].size + " bytes";
      li_size.appendChild(sz);
      kickoff(files[i]);
    }
  }
};

const digestMessage = async (algo, msgUint8) => {
  const hashBuffer = await crypto.subtle.digest(algo, msgUint8);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
};

const drawMeta = (ctx, sq, meta) => {
  const startY = ctx.canvas.height - sq;
  for (let i = 0; i < meta.length; i++) {
    const startX = i * sq;
    ctx.beginPath();
    ctx.rect(startX, startY, sq, sq);
    ctx.fillStyle = convertHexStringToRgba(meta[i]);
    ctx.fill();
    ctx.closePath();
  }
};

const fromHexString = hexString =>
  new Uint8Array(hexString.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));

// Metadata row (60 squares):
//   16 squares: calibration strip (nibbles 0–F in order)
//    4 squares: byte count (2 bytes, big-endian hex)
//   40 squares: SHA-1 of the page data
const addMetaData = (ctx, sq, hexArray, offset, numSquaresPerPage, numHalfBytesOnPage, playNext, refreshSpeed) => {
  const currOffset = offset * numSquaresPerPage;
  const data = hexArray.slice(currOffset, currOffset + numHalfBytesOnPage);
  const array = new Uint8Array(fromHexString(data.join('')));
  digestMessage('SHA-1', array).then(digest => {
    console.log(`SHA-1 of block ${offset}: ${digest}`);
    const calibration = '0123456789abcdef';
    const numBytesOnPage = Math.floor(numHalfBytesOnPage / 2).toString(16).padStart(4, '0');
    const meta = calibration + numBytesOnPage + digest;
    drawMeta(ctx, sq, meta);
    if (playNext === true && isPlaying) {
      setTimeout(next, refreshSpeed, true);
    }
  });
};

const draw = (ctx, offset, hexArray, numSquaresPerPage, numPages, playNext, refreshSpeed) => {
  const canvas = ctx.canvas;
  const w = canvas.width;
  const h = canvas.height;
  const sq = parseInt(sqWidth);

  const currOffset = offset * numSquaresPerPage;
  const nextOffset = (offset + 1) * numSquaresPerPage;
  const numHalfBytesOnPage = Math.min(hexArray.length, nextOffset) - currOffset;

  console.log(`pages: ${offset+1}/${numPages}`);
  console.log(`offsets - current: ${currOffset}, next: ${nextOffset}`);
  console.log(`number of half-bytes on page: ${numHalfBytesOnPage}`);

  // Use ImageData for a single-pass bulk pixel fill instead of per-square draw calls
  const imageData = ctx.createImageData(w, h);
  const data = imageData.data; // Uint8ClampedArray, initialized to 0 (black, transparent)

  for (let j = currOffset; j < hexArray.length && j < nextOffset; j++) {
    const idx = j % numSquaresPerPage;
    const color = convertHexStringToRgbaValues(hexArray[j]);
    const startX = (idx * sq) % w;
    const startY = Math.floor(idx * sq / w) * sq;

    for (let dy = 0; dy < sq; dy++) {
      const rowBase = (startY + dy) * w;
      for (let dx = 0; dx < sq; dx++) {
        const p = (rowBase + startX + dx) * 4;
        data[p]     = color.r;
        data[p + 1] = color.g;
        data[p + 2] = color.b;
        data[p + 3] = 255;
      }
    }
  }

  ctx.putImageData(imageData, 0, 0);
  addMetaData(ctx, sq, hexArray, offset, numSquaresPerPage, numHalfBytesOnPage, playNext, refreshSpeed);
};
