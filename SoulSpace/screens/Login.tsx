import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../App"; // 👈 import type

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigation =
    useNavigation<NativeStackNavigationProp<RootStackParamList>>();

  const handleLogin = () => {
    if (email.trim() === "" || password.trim() === "") {
      Alert.alert("Lỗi", "Vui lòng nhập email và password");
      return;
    }
    // mock login → vào MainLayout
    navigation.replace("Main");
  };
  return (
    <View style={styles.container}>
      {/* Logo */}
      <View style={styles.logoContainer}>
        <View style={styles.logoCircle}>
          <Text style={styles.logoIcon}>🎁</Text>
        </View>
        <Text style={styles.title}>SOULSPACE</Text>
      </View>

      {/* Form */}
      <TextInput
        style={styles.input}
        placeholder="Email"
        placeholderTextColor="#bbb"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        placeholderTextColor="#bbb"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      {/* Button Sign In */}
      <TouchableOpacity style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>SIGN IN</Text>
      </TouchableOpacity>

      {/* Links */}
      <TouchableOpacity>
        <Text style={styles.link}>Quên mật khẩu?</Text>
      </TouchableOpacity>

      <View style={styles.row}>
        <Text style={{ color: "#fff" }}>Bạn mới biết đến SoulSpace? </Text>
        <TouchableOpacity>
          <Text style={styles.signup}>Đăng ký</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#010440",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  logoContainer: {
    alignItems: "center",
    marginBottom: 40,
  },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 2,
    borderColor: "#ECE852",
    alignItems: "center",
    justifyContent: "center",
  },
  logoIcon: {
    fontSize: 32,
  },
  title: {
    marginTop: 10,
    fontSize: 16,
    color: "#fff",
    fontWeight: "bold",
  },
  input: {
    width: "100%",
    height: 60,
    backgroundColor: "rgba(255,255,255,0.3)",
    borderWidth: 1,
    borderColor: "#FFFFFF",
    borderRadius: 10,
    paddingHorizontal: 15,
    color: "#fff",
    marginBottom: 15,
  },
  button: {
    backgroundColor: "rgba(111, 4, 217, 0.4)", // tím 40%
    borderWidth: 1,
    borderColor: "#6F04D9", // stroke tím
    width: "100%",
    height: 50,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 10,
  },
  buttonText: {
    color: "#FFFFFF",
    fontWeight: "bold",
  },
  link: {
    color: "#ccc",
    marginTop: 15,
  },
  row: {
    flexDirection: "row",
    marginTop: 10,
  },
  signup: {
    color: "#6A5ACD",
    fontWeight: "bold",
  },
});
