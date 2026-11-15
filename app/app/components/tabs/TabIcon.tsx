import React, { Component } from 'react';
import { View, StyleSheet } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { Colors } from '../../../constants/Theme';

interface Props { name: any; focused: boolean; color: string; isMaterial?: boolean; }

export class TabIcon extends Component<Props> {
  private renderIcon() {
    const { name, color, isMaterial, focused } = this.props;
    const iconName = focused || isMaterial ? name : `${name}-outline`;
    if (isMaterial) return <MaterialCommunityIcons name={iconName} size={26} color={color} />;
    return <Ionicons name={iconName} size={24} color={color} />;
  }

  render() {
    return <View style={[styles.pill, this.props.focused && styles.active]}>
      {this.renderIcon()}
    </View>;
  }
}

const styles = StyleSheet.create({
  pill: { width: 64, height: 32, justifyContent: 'center', alignItems: 'center', borderRadius: 16 },
  active: { backgroundColor: Colors.fieldSoft }
});