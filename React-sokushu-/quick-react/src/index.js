import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import * as serviceWorker from './serviceWorker';
import MySelect from './MySelect';
// import MyTextarea from './MyTextarea';

// import MyForm from './MyForm';
// import MyHello from './MyHello';
// import MyType from './MyType';
// import MyAttrMulti from './MyAttrMulti';
// import MyHelloConponent from './MyHelloConponent';
// import MyBook from './MyBook';
// import MyProp, { Member } from './MyProps';
// import MyHelloDef from './MyHelloDef';
// import MyArticle from './MyArticle';
// import MyEvent from './MyEvent';
// import MyPool from './MyPool';
// import MyState from './MyState';
// import MyParent from './MyParent';

// multi
// const data = {
//     name: '山田権左衛門',
//     age: 18,
//     sex: '男',
// };

// comp-nest
// const book = {
//     isbn: 'WGS-JST-001',
//     title: '速習 webpack',
//     price: 454,
//     published: 'WINGSプロジェクト'
// };

// loop-basic
// const articles = [
//     {
//         url: 'https://www.atmarkit.co.jp/ait/series/9383/',
//         title: 'Angular TIPS',
//         description: '人気のJavaScriptフレームワーク「Angular」の目的別リファレンス',
//         isNew: true
//     },
// ]
// const list = articles.map((article) =>
//     <MyArticle {...article} key={article.url} />
// )

ReactDOM.render(
    // default
    <App />,

    // prop-basic
    // <MyHello />,

    // props -2
    // propsの渡し方は下記のように色々
    // <div>
    //     {/*文字列*/}
    //     <MyType value="山田" />
    //     {/*文字列*/}
    //     <MyType value={'鈴木'} />
    //     {/*数値*/}
    //     <MyType value={108} />
    //     {/*真偽値*/}
    //     <MyType value={true} />
    //     {/*配列*/}
    //     <MyType value={['うめ', 'もも', 'さくら']} />
    //     {/*オブジェクト*/}
    //     <MyType value={{ name: "山田太郎", age: 40 }} />
    //     {/*関数*/}
    //     <MyType value={() => console.log('Hoge')} />
    // </div>,

    // multi
    // <MyAttrMulti {...data} />,

    // children
    // <MyHelloConponent>
    //     <b>山田</b>
    // </MyHelloConponent>,

    // comp-nest
    // <MyBook info={book} />,

    // prop-type
    // <MyProp prop1={new Member()} />,
    // <MyProp prop1="hoge" />,
    // <MyProp prop2='男' />,
    // <MyProp prop2="hoge" />,
    // <MyProp prop3='男' />,
    // <MyProp prop3={new Member()} />,
    // <MyProp prop4={[10, 20]} />,
    // <MyProp prop4={[10, "男"]} />,
    // <MyProp prop5={{ name: '山田', age: 40, sex: '男' }} />,
    // <MyProp prop5={{ age: 40, sex: '男' }} />,

    // prop-def
    // <MyHelloDef />,
    // prop-other
    // <MyHello />,

    // loop-basic
    // <dl>
    //     {list}
    // </dl>,

    // event-basic
    // <MyEvent greet="Hello" />,
    // event-pool
    // <MyPool />,

    // state-basic 
    // <MyState />,

    // state
    // <MyParent />,

    // form
    // <MyForm />,

    // form　textarea
    // <MyTextarea />,

    // from select
    // <MySelect />,
    document.getElementById('root')
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: http://bit.ly/CRA-PWA
serviceWorker.unregister();
