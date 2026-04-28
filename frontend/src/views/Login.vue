<template>
  <div class="login-container">
    <div class="login-left">
      <div class="brand">
        <div class="logo">
          <el-icon :size="48"><ChatDotRound /></el-icon>
        </div>
        <h1>ChatApp</h1>
        <p>连接你我，即时沟通</p>
      </div>
      <div class="features">
        <div class="feature-item">
          <el-icon><Connection /></el-icon>
          <span>实时消息</span>
        </div>
        <div class="feature-item">
          <el-icon><UserFilled /></el-icon>
          <span>好友系统</span>
        </div>
        <div class="feature-item">
          <el-icon><ChatLineSquare /></el-icon>
          <span>群组聊天</span>
        </div>
      </div>
    </div>
    <div class="login-right">
      <div class="login-card">
        <h2>欢迎回来</h2>
        <p class="subtitle">登录您的账户继续聊天</p>
        <el-form :model="form" :rules="rules" ref="formRef" class="login-form">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              :prefix-icon="User"
              size="large"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              size="large"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              @click="handleLogin"
              :loading="loading"
              class="login-btn"
              size="large"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        <div class="login-footer">
          <span>还没有账号？</span>
          <router-link to="/register" class="register-link">立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "../stores/user";
import { ElMessage } from "element-plus";
import { User, Lock } from "@element-plus/icons-vue";

const router = useRouter();
const userStore = useUserStore();
const formRef = ref(null);
const loading = ref(false);

const form = reactive({
  username: "",
  password: "",
});

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    await userStore.login(form);
    ElMessage.success("登录成功");
    router.push("/");
  } catch (error) {
    ElMessage.error("登录失败，请检查用户名和密码");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
}

.login-left {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 60px;
  position: relative;
  overflow: hidden;
}

.login-left::before {
  content: "";
  position: absolute;
  width: 600px;
  height: 600px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  top: -200px;
  right: -200px;
}

.login-left::after {
  content: "";
  position: absolute;
  width: 400px;
  height: 400px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  bottom: -100px;
  left: -100px;
}

.brand {
  text-align: center;
  color: white;
  z-index: 1;
}

.logo {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  backdrop-filter: blur(10px);
}

.brand h1 {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 12px;
  letter-spacing: -0.5px;
}

.brand p {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.features {
  display: flex;
  gap: 32px;
  margin-top: 60px;
  z-index: 1;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: white;
  opacity: 0.9;
}

.feature-item .el-icon {
  font-size: 24px;
}

.feature-item span {
  font-size: 14px;
}

.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.login-card {
  width: 100%;
  max-width: 400px;
}

.login-card h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px;
}

.subtitle {
  color: #64748b;
  margin: 0 0 32px;
  font-size: 15px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e2e8f0;
  padding: 4px 16px;
  transition: all 0.3s;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  color: #64748b;
  font-size: 14px;
}

.register-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  margin-left: 4px;
  transition: color 0.3s;
}

.register-link:hover {
  color: #764ba2;
}

@media (max-width: 900px) {
  .login-left {
    display: none;
  }
}
</style>
