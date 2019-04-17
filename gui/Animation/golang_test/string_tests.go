package main

// import "C"
import "fmt"
// import "encoding/csv"
import "log"
// import "os"


var data = [][]string{{"Line1", "Hello Readers of"}, {"Line2", "golangcode.com"}}

func check(err error){
    if err != nil {
        log.Fatal(err)
    }
}

func main(){
    fmt.Println(fmt.Sprintf("Hello %d",55))
}