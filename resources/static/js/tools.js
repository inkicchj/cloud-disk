function renderSize(filesize) {
  if (filesize == 0) {
    return "0B";
  }
  var unitArr = new Array("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB");
  var index = 0;
  var srcsize = parseFloat(filesize);
  index = Math.floor(Math.log(srcsize) / Math.log(1024));
  var size = srcsize / Math.pow(1024, index);
  size = size.toFixed(2); //保留的小数位数
  return size + unitArr[index];
}

function getPreviewExt(name) {
  let office = window.config.preview.office.split(/[,，]/);
  let text = window.config.preview.text.split(/[,，]/);
  let image = window.config.preview.image.split(/[,，]/);
  let video = window.config.preview.video.split(/[,，]/);
  let audio = window.config.preview.audio.split(/[,，]/);

  let suffix = name.split(".");
  if (suffix.length > 1) {
    let ext = suffix[suffix.length - 1];
    if (text.includes(ext)) {
      return "/text";
    } else if (image.includes(ext)) {
      return "/image";
    } else if (video.includes(ext)) {
      return "/video";
    } else if (audio.includes(ext)) {
      return "/audio";
    } else if (office.includes(ext)) {
      return "/office";
    } else {
      return null;
    }
  } else {
    return null;
  }
}

function getSuffixIcon(name, is_dir) {
  let prefix = "/static/img/suffix/";
  if (is_dir) {
    return prefix + "folder.png";
  } else {
    let pList = name.split(".");
    if (pList.length == 1) {
      return prefix + "unknow.png";
    } else {
      let suffix = pList.pop();
      return prefix + suffix.toLowerCase() + ".png";
    }
  }
}


function getUnknowIcon() {
  return '/static/img/suffix/unknow.png'
}