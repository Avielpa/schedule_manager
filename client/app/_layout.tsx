import { Stack } from 'expo-router';
import { PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function Layout() {
  return (
    <PaperProvider>
      <SafeAreaProvider>
        <Stack
          screenOptions={{
            headerShown: true,
            headerTitleAlign: 'center',
          }}
        />
      </SafeAreaProvider>
    </PaperProvider>
  );
}
