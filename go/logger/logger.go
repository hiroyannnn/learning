package logger

import "fmt"

func LogOutput(message string) {
	fmt.Println(message)
}

func Log(message string) {
	LogOutput(message)
}
