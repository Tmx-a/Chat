import axios from "axios";
import { useUserStore } from "../stores/user";
import { ElMessage } from "element-plus";
import router from "../router";

const api = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const userStore = useUserStore();
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`;
  }
  const sessionId = localStorage.getItem("sessionId");
  if (sessionId) {
    config.headers["X-Session-Id"] = sessionId;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      const errorMsg = error.response.data?.error || "";
      if (status === 401) {
        const userStore = useUserStore();
        if (errorMsg.includes("会话已失效") || errorMsg.includes("Session")) {
          ElMessage.error("您的账号在其他设备登录，已被强制下线");
        } else {
          ElMessage.error("登录已过期，请重新登录");
        }
        userStore.logout();
        router.push("/login");
      } else if (status === 400) {
        ElMessage.error(errorMsg || "请求参数错误");
      } else if (status === 404) {
        ElMessage.error("资源不存在");
      } else {
        ElMessage.error(errorMsg || "服务器错误");
      }
    } else {
      ElMessage.error("网络连接失败");
    }
    return Promise.reject(error);
  },
);

export default api;
