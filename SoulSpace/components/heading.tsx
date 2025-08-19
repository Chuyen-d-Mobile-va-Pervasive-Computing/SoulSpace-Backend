import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { ArrowLeft } from "lucide-react-native";

type HeadingProps = {
    title: string;
    showBack?: boolean;
    onBackPress?: () => void;
};

const Heading: React.FC<HeadingProps> = ({ title, showBack = true, onBackPress }) => {
    return (
        <View style={styles.container}>
        {showBack && (
            <TouchableOpacity style={styles.backButton} onPress={onBackPress}>
                <ArrowLeft color="#fff" size={24} />
            </TouchableOpacity>
        )}
        <Text style={styles.title}>{title}</Text>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        width: "100%",
        flexDirection: "row",
        alignItems: "center",
        padding: 16,
        borderBottomWidth: 1,
        borderBottomColor: "#6f04d9",
        backgroundColor: "rgba(111, 4, 217, 0.3)",
    },
    backButton: {
        marginRight: 16,
    },
    title: {
        fontSize: 20,
        fontWeight: "700",
        color: "#fff",
    },
});

export default Heading;