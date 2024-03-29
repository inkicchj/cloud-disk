// 查看分享
const shareView = (mark, path, password) => {
  return request.post("/share/view", {
    mark: mark,
    path: path,
    password: password,
  });
};

// 下载文件/文件夹
const shareDownloadFetch = (mark, path, password) => {
  return fetch("/api/share/source", {
    method: "post",
    body: JSON.stringify({
      mark: mark,
      path: path,
      password: password,
    }),
    headers: {
      "Content-Type": "application/json",
    },
  });
};

function parseTime(t) {
  return moment.unix(t).format("YYYY-MM-DD HH:mm:SS");
}

document.addEventListener("alpine:init", () => {
  Alpine.data("shareData", () => ({
    dirName: null,
    url: window.location.href,
    mark: "",
    password: "",
    fileList: [],
    selected: null,
    pathList: [""],
    loading: false,
    status: 0,
    is_download: false,
    downloaded: 0,
    downloadProgress: 0,
    downloadMessage: "",
    openDLD() {
      document.getElementById("download").showModal();
    },
    closeDLD() {
      document.getElementById("download").close();
    },
    storePathList() {
      sessionStorage.setItem("shareList", JSON.stringify(this.pathList));
    },
    init() {
      this.mark = url("-1", this.url);
      let p = sessionStorage.getItem("shareList");
      if (p) {
        this.pathList = JSON.parse(p);
      } else {
        this.storePathList();
      }

      let pwd = localStorage.getItem(this.mark);
      if (pwd) this.password = pwd;

      this.getFiles();
    },
    getPath() {
      let p = this.pathList.join("/");
      if (p) {
        return p + "/";
      } else {
        return "/";
      }
    },
    getFiles() {
      this.loading = true;
      let pl = this.dirName ? this.getPath() + this.dirName : this.getPath();
      shareView(this.mark, pl, this.password)
        .then((res) => {
          this.status = 0;
          this.fileList = res.data.data;
          this.loading = false;
          if (this.dirName) this.pathList.push(this.dirName);
          this.dirName = null;
          this.storePathList();
        })
        .catch((err) => {
          this.loading = false;
          switch (err.data.code) {
            case 51100:
              this.status = 1;
              break;
            case 51101:
              this.status = 2;
              break;
            case 51102:
              this.status = 3;
              break;
          }
        });
    },
    toPath(f) {
      this.selected = null;
      if (f.is_dir) {
        if (f.name) {
          this.dirName = f.name;
          if (this.pathList.includes(this.dirName)) {
            let index = this.pathList.indexOf(this.dirName);
            this.pathList.splice(index, this.pathList.length - index);
          }
        } else {
          this.pathList = [""];
        }

        this.getFiles();
      } else {
        document.getElementById("modal-1").showModal();
      }
    },
    selectFile(f) {
      if (this.selected == f) {
        this.selected = null;
      } else {
        this.selected = f;
      }
    },
    setPassword() {
      localStorage.setItem(this.mark, this.password);
      this.getFiles();
    },
    async download() {
      if (this.is_download == false && !this.selected.is_dir) {
        this.downloadMessage = "准备下载";
        this.is_download = true;
        let p = this.getPath() + this.selected.name;
        try {
          const opts = {
            suggestedName: this.selected.name,
          };
          const handler = await window.showSaveFilePicker(opts);
          const writable = await handler.createWritable();

          let response = await shareDownloadFetch(this.mark, p, this.password);
          if (!response.ok) {
            this.downloadMessage = "下载时出错";
          } else {
            let ctype = response.headers.get("content-type");
            if (ctype == "application/json") {
              let res = await response.json();
              if (res.code == 410) {
                this.downloadMessage = res.message;
              }
            } else {
              this.openDLD();
              const reader = response.body.getReader();
              this.downloadMessage = "下载中";
              let result = true;
              while (result) {
                const { done, value } = await reader.read();
                if (done) {
                  result = false;
                  this.downloadMessage = "下载完成";
                  break;
                }
                await writable.write(value);
                this.downloaded += value.length;
                if (this.selected.size) {
                  this.downloadProgress = parseInt(
                    (this.downloaded / this.selected.size) * 100
                  );
                }
              }
              await writable.close();
            }
          }
        } catch (err) {
          this.downloadMessage = "下载时出错";
        } finally {
          this.is_download = false;
          this.downloaded = 0;
          this.downloadProgress = 0;
          this.closeDLD();
        }
      }
    },
  }));
});
