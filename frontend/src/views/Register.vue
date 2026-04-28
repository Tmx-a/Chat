<template>
  <div class="register-container">
    <div class="register-left">
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
    <div class="register-right">
      <div class="register-card">
        <h2>创建账户</h2>
        <p class="subtitle">注册开始您的聊天之旅</p>
        <el-form :model="form" :rules="rules" ref="formRef" class="register-form">
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
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="确认密码"
              :prefix-icon="Lock"
              size="large"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              @click="handleRegister"
              :loading="loading"
              class="register-btn"
              size="large"
            >
              注册
            </el-button>
          </el-form-item>
        </el-form>
        <div class="register-footer">
          <span>已有账号？</span>
          <router-link to="/login" class="login-link">立即登录</router-link>
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
  confirmPassword: "",
});

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const rules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 20, message: "用户名长度在3到20个字符", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码至少6个字符", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    { validator: validateConfirmPassword, trigger: "blur" },
  ],
};

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  loading.value = true;
  try {
    await userStore.register({ username: form.username, password: form.password });
    ElMessage.success("注册成功，请登录");
    router.push("/login");
  } catch (error) {
    ElMessage.error("注册失败，用户名可能已存在");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
}

.register-left {
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

.register-left::before {
  content: "";
  position: absolute;
  width: 600px;
  height: 600px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  top: -200px;
  right: -200px;
}

.register-left::after {
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

.register-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.register-card {
  width: 100%;
  max-width: 400px;
}

.register-card h2 {
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

.register-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.register-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e2e8f0;
  padding: 4px 16px;
  transition: all 0.3s;
}

.register-form :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
}

.register-form :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.register-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.register-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s;
}

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.register-footer {
  text-align: center;
  margin-top: 24px;
  color: #64748b;
  font-size: 14px;
}

.login-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  margin-left: 4px;
  transition: color 0.3s;
}

.login-link:hover {
  color: #764ba2;
}

@media (max-width: 900px) {
  .register-left {
    display: none;
  }
}
</style>
