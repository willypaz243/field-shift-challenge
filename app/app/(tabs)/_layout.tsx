import React, { Component } from 'react';
import { Tabs } from 'expo-router';
import { TabConfig } from '../config/TabConfig';

export default class TabLayout extends Component {
  render() {
    return <Tabs screenOptions={TabConfig.getOptions()}>
      {TabConfig.getScreens()}
    </Tabs>;
  }
}