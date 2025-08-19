import React from "react";
import { useNavigation } from "@react-navigation/native";
import { View, Text, StyleSheet } from "react-native";
import Heading from "../../components/heading";
import { Circle } from "lucide-react-native";

export default function TestDoingScreen() {
    const navigation = useNavigation();

    return (
        <View style={[styles.container, styles.viewFlexBox]}>
            <View style={[styles.view, styles.viewFlexBox]}>
                <Heading title="" showBack={true} onBackPress={() => navigation.goBack()} />
            </View>
            <View style={[styles.body, styles.bodyFlexBox]}>
                <View style={[styles.content, styles.buttonSpaceBlock]}>
                    <Text style={[styles.biTrcNghim, styles.cuHi17Typo]}>Bài trắc nghiệm MBTI (Myers–Briggs Type Indicator) dựa trên lý thuyết phân loại tính cách của Carl Jung và được phát triển bởi Isabel Briggs Myers và Katharine Cook Briggs. Bài test giúp xác định kiểu tính cách của bạn dựa trên 4 nhóm đặc điểm chính, từ đó hiểu rõ hơn về cách bạn suy nghĩ, cảm nhận và tương tác với thế giới</Text>
                    <View style={styles.question}>
                        <View style={styles.question1}>
                            <Text style={[styles.cuHi17, styles.cuHi17Typo]}>Câu hỏi 1/7</Text>
                            <Text style={[styles.aaaaaaaaaaaaaaaaaaaaa, styles.cuHi17Typo]}>aaaaaaaaaaaaaaaaaaaaa</Text>
                        </View>
                        <View style={[styles.choice, styles.choiceFlexBox]}>
                            <Text style={[styles.aaaaaaaaaaaaaaaaaaaaa, styles.cuHi17Typo]}>Có</Text>
                            <Circle style={styles.arrowArrowRightLg} width={24} height={24} />
                        </View>
                        <View style={[styles.choice, styles.choiceFlexBox]}>
                            <Text style={[styles.aaaaaaaaaaaaaaaaaaaaa, styles.cuHi17Typo]}>Có</Text>
                            <Circle style={styles.arrowArrowRightLg} width={24} height={24} />
                        </View>
                        <View style={[styles.choice, styles.choiceFlexBox]}>
                            <Text style={[styles.aaaaaaaaaaaaaaaaaaaaa, styles.cuHi17Typo]}>Có</Text>
                            <Circle style={styles.arrowArrowRightLg} width={24} height={24} />
                        </View>
                        <View style={[styles.choice3, styles.choiceFlexBox]}>
                            <Text style={[styles.aaaaaaaaaaaaaaaaaaaaa, styles.cuHi17Typo]}>Có</Text>
                            <Circle style={styles.arrowArrowRightLg} width={24} height={24} />
                        </View>
                    </View>
                </View>
                <View style={[styles.button, styles.buttonFlexBox]}>
                    <View style={[styles.button1, styles.buttonFlexBox]}>
                        <Text style={styles.lu}>Làm xong</Text>
                    </View>
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
container: {
backgroundColor: "#010440"
},
viewFlexBox: {
flex: 1,
backgroundColor: "#010440"
},
bodySpaceBlock: {
paddingHorizontal: 10,
overflow: "hidden"
},
bodyFlexBox: {
gap: 20,
alignSelf: "stretch",
flex: 1
},
buttonSpaceBlock: {
paddingVertical: 0,
paddingHorizontal: 10
},
cuHi17Typo: {
textAlign: "center",
fontFamily: "Inter-Medium",
fontWeight: "500",
fontSize: 15
},
choiceFlexBox: {
gap: 0,
justifyContent: "space-between",
flexDirection: "row",
alignItems: "center",
overflow: "hidden"
},
buttonFlexBox: {
justifyContent: "center",
height: 40,
alignSelf: "stretch",
alignItems: "center"
},
liveParentLayout: {
width: 57,
alignItems: "center"
},
hmNayTypo: {
textAlign: "left",
fontFamily: "Inter-Regular",
fontSize: 12
},
arrowArrowRightLg: {
width: 24,
height: 24,
overflow: "hidden"
},
heading: {
height: 72,
paddingVertical: 20,
flexDirection: "row",
paddingHorizontal: 10,
alignSelf: "stretch",
backgroundColor: "#010440"
},
biTrcNghim: {
color: "#fff",
alignSelf: "stretch"
},
cuHi17: {
color: "#ccc"
},
aaaaaaaaaaaaaaaaaaaaa: {
color: "#fff"
},
question1: {
borderTopLeftRadius: 10,
borderTopRightRadius: 10,
height: 60,
gap: 5,
padding: 10,
backgroundColor: "rgba(255, 255, 255, 0.3)",
alignSelf: "stretch",
overflow: "hidden"
},
choice: {
height: 40,
borderTopWidth: 1,
borderColor: "rgba(204, 204, 204, 0.3)",
justifyContent: "space-between",
borderStyle: "solid",
backgroundColor: "rgba(255, 255, 255, 0.3)",
paddingVertical: 0,
paddingHorizontal: 10,
alignSelf: "stretch"
},
choice3: {
borderBottomRightRadius: 10,
borderBottomLeftRadius: 10,
height: 40,
borderTopWidth: 1,
borderColor: "rgba(204, 204, 204, 0.3)",
justifyContent: "space-between",
borderStyle: "solid",
backgroundColor: "rgba(255, 255, 255, 0.3)",
paddingVertical: 0,
paddingHorizontal: 10,
alignSelf: "stretch"
},
question: {
alignSelf: "stretch"
},
content: {
gap: 20,
alignSelf: "stretch",
flex: 1,
alignItems: "center"
},
lu: {
fontSize: 14,
fontWeight: "700",
fontFamily: "Inter-Bold",
textAlign: "right",
color: "#fff"
},
button1: {
borderRadius: 10,
backgroundColor: "rgba(111, 4, 217, 0.3)",
borderColor: "#6f04d9",
borderWidth: 1,
borderStyle: "solid",
justifyContent: "center",
overflow: "hidden"
},
button: {
paddingVertical: 0,
paddingHorizontal: 10
},
body: {
paddingVertical: 30,
paddingHorizontal: 10,
overflow: "hidden"
},
hmNay: {
color: "#ccc"
},
livePlanetParent: {
height: 39
},
khmPh: {
color: "#fff",
alignSelf: "stretch"
},
diaryIcon: {
width: 54,
borderRadius: 20,
height: 40
},
chiaS: {
fontFamily: "Inter-Regular",
fontSize: 12,
color: "#ccc",
textAlign: "center",
alignSelf: "stretch"
},
footer: {
width: 412,
height: 48,
padding: 10,
backgroundColor: "#010440"
},
view: {
width: "100%",
height: 917,
alignItems: "center",
overflow: "hidden",
backgroundColor: "#010440"
}
});