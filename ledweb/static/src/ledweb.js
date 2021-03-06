import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';

class LedWebControls extends React.Component {
  constructor(props) {
    super(props);
    this.handleClearClick = this.handleClearClick.bind(this);
    this.handleUploadClick = this.handleUploadClick.bind(this);
    this.handleImgUrlChange = this.handleImgUrlChange.bind(this);
    this.handleWebFetchClick = this.handleWebFetchClick.bind(this);
    this.fileInput = React.createRef();
    this.state = {imgUrl: ""};
  }

  handleClearClick(e) {
    e.preventDefault();
    fetch("/led/clear", { method: "POST" });
  }

  handleUploadClick(e) {
    e.preventDefault();

    const files = this.fileInput.current.files;
    const formData = new FormData();
    formData.set("file", files[0], files[0].filename);
    fetch("/led/upload", {
      method: "POST",
      body: formData
    })
    .then(data => {
      this.props.onUpload();
    })
    .catch(error => {
      console.error(error);
    });
  }

  handleImgUrlChange(e) {
    this.setState({imgUrl: e.target.value});
  }

  handleWebFetchClick(e) {
    e.preventDefault();

    const imgUrl = this.state.imgUrl;
    const formData = new FormData();
    formData.set("url", imgUrl);
    fetch("/led/download", {
      method: "POST",
      body: formData
    })
    .catch(error => {
      console.error(error);
    })
  }

  render () {
    const imgUrl = this.state.imgUrl;

    return (
      <div className="controls">
        <div>
          <button onClick={this.handleClearClick}>Clear</button>
          <input type="file" ref={this.fileInput} />
          <button onClick={this.handleUploadClick}>Upload</button>
        </div>
        <div>
          Image URL: <input value={imgUrl} onChange={this.handleImgUrlChange} />
          <button onClick={this.handleWebFetchClick}>Fetch</button>
        </div>
      </div>
    );
  }
}

class LedWebImageControls extends React.Component {
  constructor(props) {
    super(props);
    this.handleDisplayClick = this.handleDisplayClick.bind(this);
    this.handleDeleteClick = this.handleDeleteClick.bind(this);
    this.handleXChange = this.handleXChange.bind(this);
    this.handleYChange = this.handleYChange.bind(this);
    this.state = {x: 0, y: 0}
  }

  handleDisplayClick(e) {
    e.preventDefault();
    const formData = new FormData();
    formData.set("x", this.state.x);
    formData.set("y", this.state.y);

    fetch("/led/display/" + this.props.filename, {
      method: "POST",
      body: formData
    });
  }

  handleDeleteClick(e) {
    this.props.onDelete();
  }

  handleXChange(e) {
    this.setState({x: e.target.value});
  }

  handleYChange(e) {
    this.setState({y: e.target.value});
  }

  render () {
    const x = this.state.x;
    const y = this.state.y;
    return (
      <div className="imgcontrols">
        <div>
          <button onClick={this.handleDisplayClick} disabled={this.props.deleting}>Display</button>
          x: <input value={x} onChange={this.handleXChange} size="4" />
          y: <input value={y} onChange={this.handleYChange} size="4" />
        </div>
        <div>
          <button onClick={this.handleDeleteClick} disabled={this.props.deleting}>Delete</button>
        </div>
      </div >
    );
  }
}

function LedWebImage(props) {
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (deleting) {
      fetch("/led/delete/" + props.filename, { method: "POST" })
      .then(
        (result) => {
          if (result.ok) {
            props.onDelete(props.filename);
          } else {
            console.log("error deleting: " + result.status);
          }
        },
        (error) => {
          console.log("failed to delete: " + error);
        }
      );  
    }
  });

  return (
    <div className="image deleting">
      <img src={"/image/" + props.filename} />
      <LedWebImageControls
        filename={props.filename}
        deleting={deleting}
        onDelete={() => setDeleting(true)} />
    </div>
  );
}

class LedWebImageFoo extends React.Component {
  constructor(props) {
    super(props);
    this.handleDelete = this.handleDelete.bind(this);
    this.state = {
      deleting: false
    }
  }

  handleDelete() {
    this.setState({deleting: true});
  }

  render() {
    return (
      <div className="image deleting">
        <img src={"/image/" + this.props.filename} />
        <LedWebImageControls
          filename={this.props.filename}
          deleting={this.state.deleting}
          onDelete={this.handleDelete} />
      </div>
    );
  }
}

class LedWebImages extends React.Component {
  constructor(props) {
    super(props);
    this.handleDeleteImage = this.handleDeleteImage.bind(this);
    this.handleRefresh = this.handleRefresh.bind(this);
    this.state = {
      error: null,
      isLoaded: false,
      items: []
    };
  }

  fetchImages() {
    this.setState({
      isLoaded: false
    });

    fetch("/image/")
    .then(res => res.json())
    .then(
      (result) => {
        this.setState({
          isLoaded: true,
          items: result
        });
      },
      (error) => {
        this.setState({
          isLoaded: true,
          error
        })
      }
    );
  }

  componentDidMount() {
    this.fetchImages();
  }
  
  handleRefresh() {
    this.fetchImages();
  }

  handleDeleteImage(id) {
    this.setState(prevState => ({
      items: prevState.items.filter(el => el.name != id)
    }));
  }

  render() {
    const { error, isLoaded, items } = this.state;
    if (error) {
      return <div>Error: {error.message}</div>;
    } else if (!isLoaded) {
      return <div>Loading...</div>;
    } else {
      return (
        <div>
          <LedWebControls
            onUpload={this.handleRefresh} />
          <div>
            {items.map(item => (
              <LedWebImage
                filename={item.name}
                key={item.name}
                onDelete={this.handleDeleteImage} />
            ))}
          </div>
        </div>
      );
    }
  }
}

const element = <LedWebImages />;
ReactDOM.render(
  element,
  document.getElementById("root")
);
