import { View, Text } from 'react-native';
import { Colors, Typography } from '../../constants/Theme';

export default function MiZonaScreen() {
  return (
    <View style={{ flex: 1, backgroundColor: Colors.paper2, padding: 16 }}>
      <Text style={{ ...Typography.body, color: Colors.ink }}>Pantalla Mi zona</Text>
    </View>
  );
}