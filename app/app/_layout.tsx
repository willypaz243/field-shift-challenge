import { Stack } from 'expo-router';
import { useFonts } from 'expo-font';
import { View, Text } from 'react-native';

export default function RootLayout() {
  
  const [fontsLoaded] = useFonts({
    'AtkinsonHyperlegibleNext-Regular': require('../assets/fonts/AtkinsonHyperlegibleNext-Regular.ttf'),
    'AtkinsonHyperlegibleNext-Bold': require('../assets/fonts/AtkinsonHyperlegibleNext-Bold.ttf'),
  });

  if (!fontsLoaded) {
    return <View><Text>Cargando fuentes...</Text></View>;
  }

  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
    </Stack>
  );
}