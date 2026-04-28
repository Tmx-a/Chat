import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { userApi } from "../api/modules";

export const useUserStore = defineStore("user", () => {
  const token = ref(localStorage.getItem("token") || "");
  const refreshToken = ref(localStorage.getItem("refreshToken") || "");
  const sessionId = ref(localStorage.getItem("sessionId") || "");
  const user = ref(null);

  const isLoggedIn = computed(() => !!token.value);

  async function login(credentials) {
    const res = await userApi.login(credentials);
    token.value = res.data.access;
    refreshToken.value = res.data.refresh;
    sessionId.value = res.data.session_id;
    localStorage.setItem("token", res.data.access);
    localStorage.setItem("refreshToken", res.data.refresh);
    localStorage.setItem("sessionId", res.data.session_id);
    user.value = res.data.user;
  }

  async function register(data) {
    await userApi.register(data);
  }

  async function fetchProfile() {
    const res = await userApi.getProfile();
    user.value = res.data;
  }

  async function logout() {
    try {
      await userApi.logout();
    } catch (e) {}
    token.value = "";
    refreshToken.value = "";
    sessionId.value = "";
    user.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("sessionId");
  }

  return {
    token,
    refreshToken,
    sessionId,
    user,
    isLoggedIn,
    login,
    register,
    fetchProfile,
    logout,
  };
});
