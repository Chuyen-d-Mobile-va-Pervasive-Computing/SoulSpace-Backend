import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { RouteProp, useRoute } from "@react-navigation/native";
import { ExploreStackParamList } from "../layout/MainLayout";

// 🔹 Lấy type cho route
type TestInfoRouteProp = RouteProp<ExploreStackParamList, "TestInfo">;

export default function TestInfoScreen() {
  const route = useRoute<TestInfoRouteProp>();
  const { testType } = route.params ?? {};

  return (
    <View style={styles.container}>
      <Text style={styles.text}>Trang thông tin bài test: {testType}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#010440" },
  text: { fontSize: 18, color: "#fff", fontWeight: "600" },
});