import * as React from "react";
import { StyleSheet, Text, View, TouchableOpacity } from "react-native";
import { Home, Compass, PencilLine, Users, Settings } from "lucide-react-native";

const Footer = ({ state, descriptors, navigation }: any) => {
    return (
        <View style={styles.footer}>
        {state.routes.map((route: any, index: number) => {
            const { options } = descriptors[route.key];
            const label =
            options.tabBarLabel !== undefined
                ? options.tabBarLabel
                : options.title !== undefined
                ? options.title
                : route.name;

            const isFocused = state.index === index;

            // Chọn icon theo tên route
            const getIcon = () => {
                const color = isFocused ? "#fff" : "#888";
                switch (route.name) {
                    case "Dashboard":
                    return <Home size={24} color={color} />;
                    case "Explore":
                    return <Compass size={24} color={color} />;
                    case "Diary":
                    return <PencilLine size={24} color={color} />;
                    case "Community":
                    return <Users size={24} color={color} />;
                    case "Settings":
                    return <Settings size={24} color={color} />;
                }
            };

            const onPress = () => {
                if (!isFocused) {
                    navigation.navigate(route.name);
                }
            };

            const isDiary = route.name === "Diary";

            return (
                <TouchableOpacity
                    key={route.key}
                    onPress={onPress}
                    style={[styles.tabItem]}
                >
                    <View style={isDiary ? styles.diaryIconWrapper : undefined}>
                    {getIcon()}
                    </View>
                    {!isDiary && (
                    <Text style={[styles.label, isFocused && styles.labelActive]}>
                        {label}
                    </Text>
                    )}
                </TouchableOpacity>
            );
        })}
        </View>
    );
};

const styles = StyleSheet.create({
    footer: {
        flexDirection: "row",
        justifyContent: "space-around",
        alignItems: "center",
        height: 60,
        backgroundColor: "#010440",
    },
    tabItem: {
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
    },
    label: {
        fontSize: 12,
        color: "#888",
    },
    labelActive: {
        color: "#fff",
    },
    diaryIconWrapper: {
        width: 54,
        height: 40,
        borderRadius: 20,
        borderWidth: 2,
        borderColor: "#6F04D9",
        backgroundColor: "rgba(111, 4, 217, 0.4)",
        alignItems: "center",
        justifyContent: "center",
    },
});

export default Footer;