package main

import "fmt"

type test struct {
	a []*int
}

func main() {
	var t test
	if t.a == nil {
		fmt.Println(t)
	}
	b := 1
	c := &b
	t.a = append(t.a, c)
	fmt.Println(t)

}
