class LedWebControls extends React.Component {
  constructor(props) {
    super(props);
    this.handleClearClick = this.handleClearClick.bind(this);
  }

  handleClearClick(e) {
    e.preventDefault();
    fetch("/led/clear", { method: "POST" });
  }

  render () {
    return (
      <div className="controls">
        <button onClick={this.handleClearClick}>Clear</button>
        <button>Upload</button>
      </div>
    );
  }
}

class LedWebImageControls extends React.Component {
  constructor(props) {
    super(props);
    this.handleDisplayClick = this.handleDisplayClick.bind(this);
    this.handleDeleteClick = this.handleDeleteClick.bind(this);
  }

  handleDisplayClick(e) {
    e.preventDefault();
    fetch("/led/display/" + this.props.filename, { method: "POST" });
  }

  handleDeleteClick(e) {
    this.props.onDelete();
  }

  render () {
    return (
      <div className="imgcontrols">
        <div>
          <button onClick={this.handleDisplayClick} disabled={this.props.deleting}>Display</button>
        </div>
        <div>
          <button onClick={this.handleDeleteClick} disabled={this.props.deleting}>Delete</button>
        </div>
      </div >
    );
  }
}

class LedWebImage extends React.Component {
  constructor(props) {
    super(props);
    this.handleDelete = this.handleDelete.bind(this);
    this.state = {
      deleting: false
    }
  }

  handleDelete() {
    this.setState({deleting: true});
    fetch("/led/delete/" + this.props.filename, { method: "POST" })
    .then(
      (result) => {
        if (result.ok) {
          this.props.onDelete(this.props.filename);
        } else {
          console.log("error deleting: " + result.status);
        }
      },
      (error) => {
        console.log("failed to delete: " + error);
      }
    );
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
    this.state = {
      error: null,
      isLoaded: false,
      items: []
    };
  }

  componentDidMount() {
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
    )
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
          <LedWebControls />
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
