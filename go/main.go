package main

type MailCategory int

const (
	Uncategorized MailCategory = iota
	Personal
	Work
	Spam
	Social
	Advertisements
)

type DataStore interface {
	UserNameForID(userID string) (string, bool)
}

type Logger interface {
	Log(message string)
}

type SimpleLogic struct {
	l  Logger
	ds DataStore
}

func (sl SimpleLogic) SayGoodby(userID string) (string, error) {
	sl.l.Log("Saying goodbye to " + userID)
	name, ok := sl.ds.UserNameForID(userID)
	if !ok {
		return "", errors.New("Unknown user")
	}
	return "Goodbye " + name, nil
}

func NewSimpleLogic(l Logger, ds DataStore) SimpleLogic {
	return SimpleLogic{l: l, ds: ds}
}

type Logic interface {
	SayGoodby(userID string) (string, error)
}

type Controller struct {
	l     Logger
	logic Logic
}

func (c Controller) SayGoodby(userID string) (string, error) {
	return c.logic.SayGoodby(userID)
}

func NewController(l Logger, logic Logic) Controller {
	return Controller{l: l, logic: logic}
}

func main() {
	l := NewSimpleLogger()
	ds := NewSimpleDataStore()
	logic := NewSimpleLogic(l, ds)
	controller := NewController(l, logic)
	controller.SayGoodby("1")
}
