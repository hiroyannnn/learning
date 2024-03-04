import React, { Component } from 'react';
import MyNew from './MyNew';

export default class MyArticle extends Component {
    // 条件分岐によるコード
    renderIfNew(isNew) {
        if (isNew) {
            return <MyNew />
        }
    }

    render() {
        return (
            <React.Fragment>
                <dt>
                    <a href={this.props.url}>
                        {this.props.title}</a>
                    {/* {this.props.isNew ? <MyNew /> : null} */}
                    {/* {this.props.isNew && <MyNew />} */}
                    {/* {(() => {
                        if (this.props.isNew) {
                            return <MyNew />
                        }
                    })()} */}
                    {this.renderIfNew(this.props.isNew)}
                </dt>
                <dd>
                    {this.props.description}
                </dd>
            </React.Fragment>

        );
    }
}
