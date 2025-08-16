import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { NavigationContainer } from "@react-navigation/native";
import Footer from "../components/footer";

import Dashboard from "../screens/Dashboard";
import ExploreScreen from "../screens/Explore";
import Diary from "../screens/Diary";
import Community from "../screens/Community";
import Settings from "../screens/Setting";
import TestInfoScreen from "../screens/TestInfo";

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator<ExploreStackParamList>();

// 🔹 Khai báo type cho ExploreStack
export type ExploreStackParamList = {
  Explore: undefined;
  TestInfo: { testType?: string };
};

function ExploreStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Explore" component={ExploreScreen} />
      <Stack.Screen name="TestInfo" component={TestInfoScreen} />
    </Stack.Navigator>
  );
}

export default function MainLayout() {
  return (
    <Tab.Navigator
      screenOptions={{ headerShown: false }}
      tabBar={(props) => <Footer {...props} />}
    >
      <Tab.Screen name="Dashboard" component={Dashboard} />
      <Tab.Screen name="Explore" component={ExploreStack} options={{ title: "Explore" }} />
      <Tab.Screen name="Diary" component={Diary} />
      <Tab.Screen name="Community" component={Community} />
      <Tab.Screen name="Settings" component={Settings} />
    </Tab.Navigator>
  );
}