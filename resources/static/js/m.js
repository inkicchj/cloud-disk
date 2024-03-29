// 更新配置项
const configUpdate = (param) => {
  return request.post("/setting/edit", param);
};

// 用户信息
const authMe = () => {
  return request.post("/auth/me");
};

// 更新用户名
const authUpdateName = (name) => {
  return request.post("/auth/update_name", { name: name });
};

// 更新用户密码
const authUpdatePwd = (old_pwd, new_pwd) => {
  return request.post("/auth/update_pwd", {
    old_pwd: old_pwd,
    new_pwd: new_pwd,
  });
};

// 退出登录
const authLogout = () => {
  return request.post("/auth/logout");
};

// 文件/文件夹列表
const fsList = (path, page) => {
  return request.post("/fs/list", { path: path, page: page });
};

// 文件夹列表
const fsDirs = (path, page) => {
  return request.post("/fs/dirs", { path: path, page: page });
};

// 文件夹下所有文件
const fsFiles = (path) => {
  return request.post("/fs/files", { path: path });
};

// 新建目录
const fsMkdir = (path, name) => {
  return request.post("/fs/mkdir", { path: path, name: name });
};

// 重命名文件/文件夹
const fsRename = (path, name) => {
  return request.post("/fs/rename", {
    path: path,
    name: name,
  });
};

// 文件/文件夹详情
const fsDetail = (path) => {
  return request.post("/fs/detail", { path: path });
};

// 移动文件/文件夹
const fsMove = (src_dir, dst_dir, name) => {
  return request.post("/fs/move", {
    src_dir: src_dir,
    dst_dir: dst_dir,
    name: name,
  });
};

// 复制文件/文件夹
const fsCopy = (src_dir, dst_dir, name) => {
  return request.post("/fs/copy", {
    src_dir: src_dir,
    dst_dir: dst_dir,
    name: name,
  });
};

// 清理空文件夹
const fsClearEmptyDir = (path) => {
  return request.post("/fs/clear_empty_dir", { path: path });
};

// 删除文件/文件夹
const fsRemove = (src_dir, name) => {
  return request.post("/fs/remove", { src_dir: src_dir, name: name });
};

// 获取文件资源
const fsSource = (path, mode) => {
  return request.get("/fs/source?path=" + path, {
    responseType: mode,
  });
};

// 下载文件/文件夹
const fsDownloadFetch = (path) => {
  return fetch("/api/fs/source?path=" + path, {
    method: "get",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": Cookies.get("csrf"),
    },
  });
};


// 搜索文件/文件夹
const fsSearch = (path, name, is_dir, page) => {
  return request.post("/fs/search", {
    path: path,
    name: name,
    is_dir: is_dir,
    page: page,
  });
};

// 创建存储空间
const storageNew = (
  mount_name,
  root_path,
  order,
  capacity,
  order_field,
  reverse
) => {
  return request.post("/storage/create", {
    mount_name: mount_name,
    root_path: root_path,
    order: order,
    capacity: capacity,
    order_field: order_field,
    reverse: reverse,
  });
};

// 获取排序字段
const storageOrderField = () => {
  return request.post("/storage/order_field");
};

// 存储空间列表
const storageList = () => {
  return request.post("/storage/list");
};

// 更新存储空间
const storageUpdate = (
  id,
  mount_name,
  root_path,
  order,
  capacity,
  order_field,
  reverse
) => {
  return request.post("/storage/update", {
    id: id,
    mount_name: mount_name,
    root_path: root_path,
    order: order,
    capacity: capacity,
    order_field: order_field,
    reverse: reverse,
  });
};

// 存储空间信息
const storageInfo = (id) => {
  return request.post("/storage/info", { id: id });
};

// 激活存储空间
const storageEnable = (id) => {
  return request.post("/storage/enable", { id: id });
};

// 关闭存储空间
const storageDisable = (id) => {
  return request.post("/storage/disable", { id: id });
};

// 激活存储空间
const storageDelete = (id) => {
  return request.post("/storage/delete", { id: id });
};

// 创建分享链接
const shareNew = (path, password, expired) => {
  return request.post("/share/create", {
    path: path,
    password: password,
    expired: expired,
  });
};

// 获取分享列表
const shareList = (page) => {
  return request.post("/share/list", { page: page });
};

// 获取分享信息
const shareInfo = (id) => {
  return request.post("/share/info", { id: id });
};

// 删除分享链接
const shareDelete = (id) => {
  return request.post("/share/delete", { id: id });
};

// 获取分享链接过期时间
const shareExpired = () => {
  return request.post("/share/expired");
};

// 创建上传任务
const uploadTaskCreate = (
  path,
  web_path,
  name,
  size,
  modified,
  mime_type,
  mode,
  wipe
) => {
  return request.post("/upload_task/create", {
    path: path,
    web_path: web_path,
    name: name,
    size: size,
    modified: modified,
    mime_type: mime_type,
    mode: mode,
    wipe: wipe
  });
};

// 上传任务列表
const uploadList = () => {
  return request.post("/upload_task/list");
};

// 流式上传文件
const uploadStream = (session_id, file, onProgress = null) => {
  return request.post(`/upload_task/stream/${session_id}`, file, {
    onUploadProgress: (progressEvent) => {
      if (onProgress != null) {
        onProgress(progressEvent);
      }
    },
  });
};

// 分片上传文件
const uploadChunk = (session_id, chunk_cur, file, onProgress = null) => {
  return request.post(`/upload_task/chunk/${session_id}/${chunk_cur}`, file, {
    onUploadProgress: (progressEvent) => {
      if (onProgress != null) {
        onProgress(progressEvent);
      }
    },
  });
};

// 删除上传任务
const deleteUpload = (session_id) => {
  return request.post("/upload_task/delete", { session_id: session_id });
};
