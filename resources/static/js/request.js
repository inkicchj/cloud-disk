const request = axios.create({
  baseURL: "/api",
});

// 添加请求拦截器
request.interceptors.request.use(
  function (config) {
    // 在发送请求之前做些什么
    const csrf = Cookies.get("csrf");
    if (csrf) config.headers["X-CSRF-Token"] = csrf;
    return config;
  },
  function (error) {
    // 对请求错误做些什么
    return Promise.reject(error);
  }
);

// 添加响应拦截器
request.interceptors.response.use(
  function (response) {
    // 2xx 范围内的状态码都会触发该函数。
    // 对响应数据做点什么
    const code = response.data.code;
    
    switch (code) {
      case 410:
        $vh.warning(response.data.message);
        break;
      case 425:
        $vh.warning(response.data.message);
        break;
      case 430:
        $vh.error(response.data.message);
        break;
      case 51100:
        break;
      case 51101:
        break;
      case 51102:
        break;
      case 52001:
        break;
      case 50000:
        $vh.warning(response.data.message);
        break;
      case 52000:
        $vh.warning(response.data.message);
        break;
      case 200:
        return response;
    }
    return Promise.reject(response);
  },
  function (error) {
    // 超出 2xx 范围的状态码都会触发该函数。
    // 对响应错误做点什么
    return Promise.reject(error.response);
  }
);
