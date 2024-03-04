
import React, { Component } from 'react';

export default class MyEvent extends Component {
    show(suffix, e) {
        console.log(`${this.props.greet},${e.target.value}${suffix}!!`)
    }
    render() {
        return (
            <form>
                <label htmlFor="txtName">名前：</label>
                {/* 入力変更時にshowメソッドを呼び出し */}
                <input id='txtName' type="text" onChange={this.show.bind(this, "さん")}
                />
            </form>
        );
    }
}
