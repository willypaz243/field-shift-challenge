import React, { Component } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { Colors, Typography } from '../../../constants/Theme';
import { HeaderLocation } from './HeaderLocation';
import { Bell } from '../../../src/ui/Bell';
import { LangToggle } from '../../../src/ui/LangToggle';

export class HeaderLeft extends Component {
  private renderBrand() {
    return <View style={styles.row}>
      <MaterialCommunityIcons name="corn" size={28} color={Colors.cornGold} />
      <Text style={styles.brand}>Choclito</Text>
    </View>;
  }

  private renderLocation() {
    return <View style={styles.row}>
      <Ionicons name="location-outline" size={18} color={Colors.ink2} />
      <HeaderLocation style={styles.loc} />
    </View>;
  }

  render() {
    return <View style={{ gap: 4, flexShrink: 1 }}>
      {this.renderBrand()}
      {this.renderLocation()}
    </View>;
  }
}

export function HeaderRight() {
  return <View style={[styles.row, { gap: 12 }]}>
    <Bell />
    <LangToggle compact />
  </View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  brand: { fontFamily: 'AtkinsonHyperlegibleNext-Bold', fontSize: 22, color: Colors.fieldDeep },
  loc: { ...Typography.meta, color: Colors.ink2 },
});