---
title: "Fun with Go and JSON"
date: 2023-03-25
tags: 
  - "etl"
  - "golang"
  - "json"
---

## Intro

So lets go over how to work with JSON in Go. This article is intended for those with at least some basic Golang knowledge, or at the minimum some basic programming knowledge. If you are coming from Python, JS, or another weakly typed language, working with JSON in Golang is going to look a little different. I’m going to try to explain everything you need to get started working with JSON objects in golang

## What is JSON?

What is JSON? For starters, it stands for JavaScript Object Notation, a way to format objects in a standardized format. JSON is one of the most common ways to communicate data between systems, for instance between a front-end and a back-end, or between two completely unconnected systems such as retrieving data from a 3rd party application. When accessing most modern-day API’s, whether to fetch data on stocks, prices at an online retailer, or anything else you might use an API for, that data is most commonly going to be given to you in JSON format. So what does JSON look like?

- Data is represented in name:value pairs

- Curly braces hold objects and each name is followed by a colon, the name/value pairs are separated by a comma

- Square brackets hold arrays and values are separated by a comma.

Here is an example of a JSON object:

```jscript
{
    "book": [
      {
        "id": "01",
        "language": "Java",
         "edition": "third",
         "author": "Herbert Schildt"
      },
      {
       "id": "07",
       "language": "C++",
       "edition": "second",
       "author": "E.Balagurusamy"
      }
   ]
}
```

## Create the structs

To start off, creating the struct to handle the JSON data can be a little daunting. If you are working with some simple JSON data, you may wish to use a [JSON to Struct converter](https://mholt.github.io/json-to-go/), but keep in mind those types of tools do not typically convert complex data very well, so use them very carefully. In this case, we are just going to create our own structs to match the data.  
  
Due to Golang being a strongly-typed language, we need to create [a struct](https://gobyexample.com/structs) to describe the data and it's types before loading it. The struct describes the JSON object and the types of data encoded inside of it. To create a struct to handle the JSON data described above, we first need to describe an individual book, and then we need to describe the object which holds multiple books. I wanted to choose a nested data type like this so that you can fully appreciate how to encode the data, as you are not very likely to receive 1 level deep JSON data in the real world. So what do these 2 structs look like? Let's take a look:

```go
// Describe a collection of books
type Books struct {
	Books	[]Book `json:"book"`
}

// Describe an individual book
type Book struct {
	ID       string `json:"id"`
	Language string `json:"language"`
	Edition  string `json:"edition"`
	Author   string `json:"author"`
}
```

There is another way we can create the structs inline as well, however, this changes the data structure slightly. For the remainder of the article, we will be using the above structs as they are a little more clear for a beginner, IMHO, but it is good to be aware it can be done both ways:

```
type Books struct {
	Book []struct {
		ID       string `json:"id"`
		Language string `json:"language"`
		Edition  string `json:"edition"`
		Author   string `json:"author"`
	} `json:"book"`
}
```

## Load data from file

We now have our struct, so how do we actually load some data into it and start manipulating it? There are various ways to get JSON data, as mentioned previously the most common way is via API, but let's start with something a little simpler and just load a file. I'm just going to throw the JSON data into a file called test\_data.json, and then let's load it into our struct. Note that taking a JSON string and decoding it into our struct is a process called "unmarshalling", and converting Go data into a JSON string is called "marshalling", which you can read more about [here](https://linuxhint.com/marshal-unmarshal-golang/). To do this, we are going to use the standard Go package "encoding/json".  
  
So first things first, we need to load the file, which can be done with a simple function. In some cases, you would want to load individual parts of the file to get specific data, however for simplicities sake we will load the entire thing. the ReadFile function returns a \[\]byte type, or byte slice, which is the type we need in order to unmarshall.

```go
// Load file from disk, convert to string
func readFile(filename string) (contents []byte) {
	contents, err := os.ReadFile(filename)
	if err != nil {
		fmt.Printf("File was not able to be loaded. Error: %s", err)
		os.Exit(1)
	}
	return
}
```

## Unmarshall file data into struct

At this point, we have our data loaded into memory with the type \[\]byte, which as stated is exactly what we need. A quick sidenotes for the curious: if we had used os.Open(filename) instead, the returned value would have been an \*os.File type, and we would have then had to convert it to the \[\]byte type with ioutil.ReadAll(), so we can just use os.ReadFile instead - we can do this because we are loading the whole file instead of parts of it. Seeing as we already have the type we need, lets move on to the actual unmarshalling of the data into our struct so we can more readily work with it.

```go
func unmarshallData(bdata []byte) (sdata Books) {
	err := json.Unmarshal(bdata, &sdata)
	if err != nil {
		fmt.Printf("Cannot unmarshall data. Error:\n%s", err)
	}
	return
}
```

## Manipulating the data

Now that we have our json data loaded into our struct, it can be accessed and manipulated like any other standard Go struct. In our specific example, the first book can be accessed with `jdata.Books[0]`, and it's author could be accessed with `jdata.Books[0].Author`.  
  
Following up with that, say we wanted to change the Edition of the first book and update it from the third edition to the fourth. for simplicity, we'll use our previously created functions, and change the edition in the main function:

```go
func main() {
	jsonFile := readFile("test_data.json")
	myBooks := unmarshallData(jsonFile)

	fmt.Printf("Book 1 before transform:\t%v\n", myBooks.Books[0].Edition)
	myBooks.Books[0].Edition = "fourth"
	fmt.Printf("Book 1 after transform:\t\t%v\n", myBooks.Books[0].Edition)
}

Output:
go run main.go
Book 1 before transform:        {01 Java third Herbert Schildt}
Book 1 after transform:         {01 Java fourth Herbert Schildt}
```

## Writing data as JSON

At this point, we can load and manipulate the data, now we just need to be able to convert our struct back into a JSON object so we can either write it to a file, or send it along to whatever data source is the end target. If you are performing some sort of ETL (Extract, Transform, Load) operation, a very common task, then it's important to be able to turn the data back into JSON so that it can be understood by external programs or systems, such as another API. How do we do that? You might have guessed that we're going to use the oppose of the unmarshall function, marshall - you would be correct. So first, lets marshall our data back into json, which is very similar to our unmarshall function:

```go
func marshallData(sdata *Books) (jdata []byte) {
	jdata, err := json.Marshal(sdata)
	if err != nil {
		fmt.Printf("Error marshalling struct to json. Error:%v\n", err)
		os.Exit(1)
	}
	return
}
```

In this case to keep things simple, we are just going to write the data to a separate file. In real life applications of this, you likely would be sending this data out to an API endpoint, which typically is going to handle storing the data in a database of some sort, but to keep this article focused we're just going to write to a file. To do that, we'll use this simple write function:

```
func writeFile(filename string, data []byte) (contents []byte) {
	err := os.WriteFile(filename, data, 0644)
	if err != nil {
		fmt.Printf("Unable to write data to file. Error: %s", err)
		os.Exit(1)
	}
	return
}
```

We now have all of the functions we need, so lets update our main function with a few new entries, namely the file we're going to write to, and then of course we need to actually call the functions we made:

```go
func main() {
	// define the file to read from
	inFile := readFile("test_data.json")
	// file to write to
	outFile := "changed_data.json"
	// struct with data loaded
	myBooks := unmarshallData(inFile)

	fmt.Printf("Book 1 before transform:\t%v\n", myBooks.Books[0])
	// Change edition from third to fourth
	myBooks.Books[0].Edition = "fourth"
	fmt.Printf("Book 1 after transform:\t\t%v\n", myBooks.Books[0])

	// Marshall struct back into JSON
	outData := marshallData(&myBooks)

	// Write to the output file with the changed data
	writeFile(outFile, outData)
}
```

## Conclusion

So there we have it! You now have all of the tools you need to work with JSON, and the basics to perform ETL tasks. If you would like to to view all of the code together, you can find it on my [Gitlab here](https://gitlab.com/jhaxdev/fun_with_json_go).  
  
If I have left anything out, made a mistake (very, very likely!) or if you just have questions, please leave me a comment and I'll do my best to respond.  
  
Happy Hacking!
