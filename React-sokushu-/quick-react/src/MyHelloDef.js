import React, { Component } from 'react';
import PropTypes from 'prop-types';
import MyHello from './MyHello';

export default class MyHelloDef extends Component {
    // 描画する内容を定義
    render() {
        return <div>こんにちは、{this.props.name}さん！</div>;
    }
}
// 型情報の定義
MyHelloDef.propTypes = {
    name: PropTypes.string
};
// 既定値の定義
MyHelloDef.defaultProps = {
    name: '名無権兵衛'
};
