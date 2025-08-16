import React from "react";
import { View, Text, StyleSheet, Image, TouchableOpacity, ScrollView } from "react-native";
import { ArrowLeft } from "lucide-react-native";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
    Explore: undefined;
    TestInfo: { testType: string };
};

export default function ExploreScreen() {
    const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <ArrowLeft size={24} color="#fff" />
                <Text style={styles.headerTitle}>Khám phá</Text>
            </View>

            {/* Body */}
            <ScrollView style={styles.body} contentContainerStyle={{ paddingBottom: 80 }}>
                {cards.map((item, idx) => (
                    <View key={idx} style={styles.card}>
                        <Image source={item.image} style={styles.cardImage} resizeMode="cover" />
                        <View style={styles.cardContent}>
                            <Text style={styles.cardTitle}>{item.title}</Text>
                            <Text style={styles.cardDesc}>{item.desc}</Text>
                        </View>

                        {/* Button dẫn đến do.tsx */}
                        <TouchableOpacity
  style={styles.cardButton}
  onPress={() => navigation.navigate("TestInfo", { testType: item.title })}
>
  <Text style={styles.cardButtonText}>Thực hiện bảng câu hỏi</Text>
</TouchableOpacity>

                    </View>
                ))}
            </ScrollView>
        </View>
    );
}

const cards = [
    {
        title: "MBTI - Khám phá tính cách của bạn",
        desc: "Bạn là người hướng nội hay hướng ngoại? ...",
        image: require("../assets/mbti.png"),
    },
    {
        title: "PHQ-9 – Đo lường mức độ trầm cảm",
        desc: "Cảm thấy buồn bã, mất động lực ...",
        image: require("../assets/phq.png"),
    },
    {
        title: "GAD-7 – Đánh giá mức độ lo âu",
        desc: "Thường xuyên lo lắng, bồn chồn ...",
        image: require("../assets/anxiety.png"),
    },
    {
        title: "PSS – Đo mức độ căng thẳng",
        desc: "Cuộc sống bận rộn khiến bạn cảm thấy áp lực? ...",
        image: require("../assets/pss.png"),
    },
];

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: "#010440" },
    header: {
        flexDirection: "row",
        alignItems: "center",
        padding: 16,
        borderBottomWidth: 1,
        borderBottomColor: "#6f04d9",
        backgroundColor: "rgba(111, 4, 217, 0.3)",
    },
    headerTitle: { fontSize: 20, fontWeight: "700", color: "#fff", marginLeft: 10 },

    body: { flex: 1, padding: 16 },
    card: {
        backgroundColor: "rgba(255,255,255,0.2)",
        borderRadius: 12,
        padding: 10,
        marginBottom: 20,
    },
    cardImage: { width: "100%", height: 120, borderRadius: 8 },
    cardContent: { marginVertical: 10 },
    cardTitle: { fontSize: 16, fontWeight: "700", color: "#fff", marginBottom: 5 },
    cardDesc: { fontSize: 14, color: "#ddd" },
    cardButton: {
        backgroundColor: "rgba(111, 4, 217, 0.6)",
        borderRadius: 8,
        paddingVertical: 12,
        alignItems: "center",
        marginTop: 10,
    },
    cardButtonText: { color: "#fff", fontWeight: "600", fontSize: 14 },
});