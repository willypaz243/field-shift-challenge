import { View, Text } from 'react-native';
import { Colors, Typography } from '../../constants/Theme';

export default function HoyScreen() {
  return (
    <View style={{ flex: 1, backgroundColor: Colors.paper, padding: 16 }}>
      <Text style={{ ...Typography.body, color: Colors.ink }}>Pantalla Hoy</Text>
    </View>
  );
}