import React, { Component } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { Colors, Typography } from '../../../constants/Theme';
import { HeaderLocation } from './HeaderLocation';

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
    return <View style={{ gap: 4 }}>
      {this.renderBrand()}
      {this.renderLocation()}
    </View>;
  }
}

export class HeaderRight extends Component {
  private renderBell() {
    return <Pressable style={styles.bell}>
      <Ionicons name="notifications-outline" size={26} color={Colors.ink} />
      <View style={styles.badge}><Text style={styles.badgeTxt}>3</Text></View>
    </Pressable>;
  }

  private renderLang() {
    return <Pressable style={styles.lang}>
      <Text style={styles.langTxt}>ES</Text>
    </Pressable>;
  }

  render() {
    return <View style={[styles.row, { gap: 12 }]}>
      {this.renderBell()}
      {this.renderLang()}
    </View>;
  }
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  brand: { fontFamily: 'AtkinsonHyperlegibleNext-Bold', fontSize: 22, color: Colors.fieldDeep },
  loc: { ...Typography.meta, color: Colors.ink2 },
  bell: { minWidth: 56, minHeight: 56, justifyContent: 'center', alignItems: 'center' },
  badge: { position: 'absolute', top: 8, right: 8, backgroundColor: '#D9381E', borderRadius: 12, width: 20, height: 20, justifyContent: 'center', alignItems: 'center' },
  badgeTxt: { color: Colors.paper, fontSize: 12, fontFamily: 'AtkinsonHyperlegibleNext-Bold' },
  lang: { backgroundColor: Colors.fieldDeep, borderRadius: 28, width: 56, height: 56, justifyContent: 'center', alignItems: 'center' },
  langTxt: { color: Colors.paper, fontFamily: 'AtkinsonHyperlegibleNext-Bold', fontSize: 17 }
});