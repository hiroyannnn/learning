
import React, { Component } from 'react';

export default class MyList extends Component {
    constructor(props) {
        super(props);
        // Stateを初期化
        this.state = {
            fruit: 'apple',
        };
        this.handleChange = this.handleChange.bind(this);
        this.show = this.show.bind(this);
    }
    // 選択ボックスの反映時に入力値をStateに反映
    handleChange(e) {
        this.setState({
            [e.target.name]: e.target.value
        });
    }
    // [送信]ボタンクリック時に入力値をログ出力
    show() {
        console.log(`好きな果物：${this.state.fruit}`);
    }
    render() {
        return (
            <form>
                <label htmlFor="fruit">好きな果物：</label>
                <select id="fruit" name="fruit" value={this.state.fruit}
                    onChange={this.handleChange}>
                    <option value="apple">りんご</option>
                    <option value="orange">オレンジ</option>
                    <option value="melon">メロン</option>
                    <option value="grape">ぶどう</option>
                    <option value="strawberry">いちご</option>
                </select>
                <button type="button" onClick={this.show}>送信
                </button>
            </form>
        );
    }
}
