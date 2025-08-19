import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import MainLayout from "./layout/MainLayout";

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {/* Screen KHÔNG có Footer */}
        {/* <Stack.Screen name="Login" component={Login} />
        <Stack.Screen name="Register" component={Register} /> */}

        {/* Screen Có Footer */}
        <Stack.Screen name="Main" component={MainLayout} />
      </Stack.Navigator>
    </NavigationContainer>

  );
}