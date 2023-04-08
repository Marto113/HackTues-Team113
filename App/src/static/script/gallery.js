function clicked_img(img, fp) {
    console.log(img.src);
    var top = document.getElementById('top');
    top.src = img.src;
    top.hidden = false;


    if (img.naturalWidth < screen.width * 0.3 && img.naturalHeight < screen.height * 0.3) {
        top.width = img.naturalWidth;
        top.height = img.naturalHeight;

    } else {
        top.width = screen.width * 0.3;
        top.height = img.naturalHeight / img.naturalWidth * top.width;
    }

    document.getElementById('close').hidden = false;
}


function do_close() {
    document.getElementById('top').hidden = true;
    document.getElementById('close').hidden = true;
}

function delete_image(type) {
    var img_src = document.getElementById("top").getAttribute("src");
    var filename = img_src.split('/').pop();
    window.location.href = type + "/delete/" + filename;
}