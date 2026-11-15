import { Stack } from 'expo-router';
import { useFonts } from 'expo-font';
import { View, Text } from 'react-native';
import { OfflineProvider, useOfflineReady } from '../src/offline/provider';

export default function RootLayout() {
  
  const [fontsLoaded] = useFonts({
    'AtkinsonHyperlegibleNext-Regular': require('../assets/fonts/AtkinsonHyperlegibleNext-Regular.ttf'),
    'AtkinsonHyperlegibleNext-Bold': require('../assets/fonts/AtkinsonHyperlegibleNext-Bold.ttf'),
  });

  if (!fontsLoaded) {
    return <View><Text>Cargando fuentes...</Text></View>;
  }

  return (
    <OfflineProvider>
      <ReadyStack />
    </OfflineProvider>
  );
}

// Screens read the local database and the farm answers, so they wait for both.
function ReadyStack() {
  if (!useOfflineReady()) return null;
  return (
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="ubicar" options={{ headerShown: false }} />
        <Stack.Screen name="agua" options={{ headerShown: false }} />
        <Stack.Screen name="avisos" options={{ headerShown: false }} />
        <Stack.Screen name="cultivo/[id]" options={{ headerShown: false }} />
      </Stack>
  );
}