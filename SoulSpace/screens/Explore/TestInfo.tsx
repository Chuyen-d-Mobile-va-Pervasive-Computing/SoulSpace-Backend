import React from "react";
import { View, Text, StyleSheet, Image, TouchableOpacity } from "react-native";
import { RouteProp, useRoute, useNavigation } from "@react-navigation/native";
import { ExploreStackParamList } from "../../layout/MainLayout";
import Heading from "../../components/heading";
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

// 🔹 Lấy type cho route
type TestInfoRouteProp = RouteProp<ExploreStackParamList, "TestInfo">;
// 🔹 Lấy type cho navigation
type TestInfoNavProp = NativeStackNavigationProp<ExploreStackParamList, "TestInfo">;

export default function TestInfoScreen() {
  const route = useRoute<TestInfoRouteProp>();
  const navigation = useNavigation<TestInfoNavProp>();

  const testType = route.params?.testType ?? "";

  return (
    <View style={styles.container}>
      <Heading 
        title="Bảng câu hỏi" 
        showBack={true} 
        onBackPress={() => navigation.goBack()}
      />
      <View style={styles.view}>
        <View style={styles.writing}>
          <Image
            style={[styles.minigameIcon, styles.button1Layout]}
            resizeMode="cover"
            source={
              testType.includes("MBTI")
                ? require("../../assets/mbti.png")
                : testType.includes("PHQ-9")
                ? require("../../assets/phq.png")
                :testType.includes("GAD")
                ? require("../../assets/anxiety.png") 
                : require("../../assets/pss.png")
            }
          />
        </View>
        <View style={[styles.content, { paddingHorizontal: 10, paddingVertical: 0 }]}>
          <Text style={[styles.mbtiKhm, styles.mbtiKhmFlexBox]}>
            {testType.includes("PHQ-9") ? "PHQ9- Đo lường mức độ trầm cảm" : testType.includes("PSS") ? "PSS - Đo lường mức độ căng thẳng" :testType.includes("GAD") ? "GAD - Đo lường mức độ lo âu" : "MBTI - Khám phá tính cách của bạn"}
          </Text>
          <Text style={[styles.biTrcNghim, styles.mbtiKhmFlexBox]}>
            {testType.includes("PHQ-9") ? "Bài trắc nghiệm PHQ..." : testType.includes("PSS") ? "Bài trắc nghiệm PSS..." :testType.includes("GAD") ? "Bài trắc nghiệm GAD..." : "Bài trắc nghiệm MBTI (Myers–Briggs Type Indicator) dựa trên lý thuyết phân loại tính cách..."}
          </Text>
        </View>
        <View style={[styles.button, styles.buttonFlexBox]}>
          <TouchableOpacity style={[styles.button1, styles.buttonFlexBox]} onPress={() => navigation.navigate("TestDoing", { testType: testType })}>
            <Text style={styles.lu}>Bắt đầu</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#010440" },
  text: { fontSize: 18, color: "#fff", fontWeight: "600" },
  body: {
    flex: 1
  },
  button1Layout: {
    borderRadius: 10,
    overflow: "hidden"
  },
  buttonSpaceBlock: {
    paddingVertical: 0,
    paddingHorizontal: 10
  },
  mbtiKhmFlexBox: {
    textAlign: "center",
    color: "#fff",
    alignSelf: "stretch"
  },
  buttonFlexBox: {
    justifyContent: "center",
    height: 40,
    alignItems: "center",
    alignSelf: "stretch"
  },
  minigameIcon: {
    maxWidth: "100%",
    height: 290,
    alignSelf: "stretch",
    width: "100%",
    borderRadius: 10
  },
  writing: {
    alignSelf: "stretch",
    overflow: "hidden"
  },
  mbtiKhm: {
    fontSize: 20,
    fontFamily: "Inter-Bold",
    fontWeight: "700",
    textAlign: "center"
  },
  biTrcNghim: {
    fontSize: 15,
    fontWeight: "500",
    fontFamily: "Inter-Medium"
  },
  content: {
    alignItems: "center",
    paddingVertical: 0,
    alignSelf: "stretch",
    gap: 20,
    flex: 1
  },
  lu: {
    fontSize: 14,
    textAlign: "right",
    color: "#fff",
    fontFamily: "Inter-Bold",
    fontWeight: "700"
  },
  button1: {
    backgroundColor: "rgba(111, 4, 217, 0.3)",
    borderStyle: "solid",
    borderColor: "#6f04d9",
    borderWidth: 1,
    borderRadius: 10,
    overflow: "hidden"
  },
  button: {
    paddingVertical: 0,
    paddingHorizontal: 10
  },
  view: {
  paddingVertical: 30,
    gap: 20,
    paddingHorizontal: 10,
    overflow: "hidden",
    width: "100%",
    flex: 1
  }
});