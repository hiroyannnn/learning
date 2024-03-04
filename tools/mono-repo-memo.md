# モノレポ作業メモ

```shell
REPO_URL=https://github.com/hiroyannnn/React-native-study.git
REPO_DIR=React-native-study

# 統合したいリポジトリを一時的なブランチにフェッチ
git remote add $REPO_DIR $REPO_URL
git fetch $REPO_DIR

# 統合したいリポジトリの主要なブランチ（例：masterやmain）を、指定されたディレクトリにマージ
git checkout -b merge-$REPO_DIR
git read-tree --prefix=$REPO_DIR/ -u $REPO_DIR/master 
# 変更をコミットし、mainブランチにマージ
git commit -m "統合したリポジトリ $REPO_DIR を追加"
git checkout main
git merge merge-$REPO_DIR

# 一時的なブランチとリモートを削除
git branch -d merge-$REPO_DIR
git remote remove $REPO_DIR

git push 
gh repo delete hiroyannnn/$REPO_DIR
```
