import React, { Component } from 'react';
import { View, StyleSheet } from 'react-native';
import { HeaderLeft, HeaderRight } from './HeaderElements';
import { Colors } from '../../../constants/Theme';

export class GlobalHeader extends Component {
  render() {
    return <View style={styles.container}>
      <HeaderLeft />
      <HeaderRight />
    </View>;
  }
}

const styles = StyleSheet.create({
  container: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: Colors.paper, paddingTop: 48, paddingBottom: 16, paddingHorizontal: 16, borderBottomWidth: 1, borderBottomColor: Colors.line }
});