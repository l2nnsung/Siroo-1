from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Post, Comment, Tag
from accounts.models import User, User_profile
from django.utils import timezone
from datetime import datetime
#hot_tag를 위해 db.models에서 Count import해옴.
from django.db.models import Count
#login_required 기능을 위해 import
from django.contrib.auth.decorators import login_required


def index(request):

    posts = Post.objects.all().order_by('-created_at')
    
    #전체 태그에서 가장 많이 쓰인 태그 불러오기    
    # taged_post가 없는 경우 태그 목록에 노출 되지 않도록.
    tags=Tag.objects.exclude(taged_post__isnull=True).annotate(num_posts=Count('taged_post')).order_by('-num_posts')
    tags=list(tags)


    hot_tags = tags[0:9]

    context = {        
        'posts' : posts,
        'hot_tags' : hot_tags,
    }
    
    return render(request, 'posts/index.html', context)

@login_required
def detail(request, post_id):

    post = Post.objects.get(id=post_id)
    #detail templates에서 사용하기 위해 context에 제공해야하기에 쿼리셋을 리스트형태로 받아옴.
    tags = list(post.taginpost.all())
    #연관 tag의 id를 int형태로 받아옴.
    tag_ids =[*map(lambda tag:tag.id, list(post.taginpost.all()))]
    
    if len(tag_ids) > 0:
        tag_id = tag_ids.pop()
        tag = Tag.objects.get(id=tag_id)
        posts = tag.taged_post.all()
    else:
        pass

    #댓글 뷰 기능
    comments = post.comment_set.all().order_by('-id')

    #좋아요 뷰 기능
    likedusers = list(post.liked_users.all())
    likedusers_nicks = [*map(lambda user:user.nickname, list(post.liked_users.all()))]

    if len(likedusers_nicks) > 0:
        likedusers_nick = likedusers_nicks.pop()
        print(likedusers_nick)

    liked_user = None
    if len(likedusers) > 0:
        if len(likedusers) == 1:
            for a in likedusers:
                liked_user = likedusers_nick + " 님이 좋아합니다"
        else:
            liked_user = likedusers_nick + " 님 외 " + str(len(likedusers)) + "명이 좋아합니다."
    else:
        liked_user = ""

    context = {
        'post' : post,
        'comments' : comments,
        'liked_user' : liked_user,
        'tags' : tags,
    }
    return render(request, 'posts/detail.html', context)

@login_required
def new(request):

    return render(request, 'posts/new.html')

@login_required
def create(request):

    context = {} 

    user = request.user
    tag = request.POST['tag']
    body = request.POST['body']
    body_tag = body + ' ' + tag
    post = Post(user= user, body = body_tag)
    if len(body) < 1 :
        context['error'] = '한 글자 이상은 작성해주세요'
    else:
        if body.count('#') < 6:
            post.save()
            return redirect('posts:tagforpost', post_id=post.id)
        else:            
            context['error'] = '태그(#)가 5개를 초과할 수 없습니다'
            context['body'] = body            
  
    #바로 detail페이지로 가지 않고, tag저장 후 가기 위해서 tagforpost로 이동
    return render(request, 'posts/new.html', context) 

def tagforpost(request, post_id):

    post = Post.objects.get(id=post_id)
    #본문을 str으로 바꾼 뒤, 띄어쓰기대로 Split해서 list로 저장함.    
    body = str(post.body).split()

    taglist = list()
    original_tags = list()

    #태그가 있는지 확인하는 과정
    if len(body) > 0 :

        for i in body:
            if i == '#':
                pass
            else :
                if i.count('#') > 0:
                    taglist.append(i)
                else:
                    pass

    #글 수정시 태그 중복 저장 방지(새로 작성된 글은 이 과정이 생략됨)
        if post.taginpost.all():
            for tag in list(post.taginpost.all()):
                original_tags.append(tag)
            if taglist == original_tags:
                return redirect('posts:detail', post_id=post.id)
            else:
                tag = post.taginpost.all()
                tag.delete()
        else:
            pass
    #-------------------------------------------------------------             
    #태그가 있을 시, #을 빼내고 문자열로 바꿔주어서 태그에 저장함.
        for i in taglist: 
            x = i.split('#')
            del x[0]
            tag_text = ''.join(x)

            #태그를 스플릿해서 '#'이 빠진 스트링 형태로 tag에 저장함
            tag=Tag(tag=tag_text)
            post.save()
            "태그"
            
            #태그가 기존에 있는 태그면, 쿼리셋에 추가만 해주고,
            #태그가 기존에 없는 태그라면 태그를 저장한 뒤에 쿼리셋에 추가함.
            try:
                tag = Tag.objects.get(tag=tag_text)
                
            except Tag.DoesNotExist:
                tag.save()

            post.taginpost.add(tag)
    
    return redirect('posts:detail', post_id=post.id)

@login_required
def edit(request, post_id):
    try:
        post = Post.objects.get(id=post_id, user=request.user)
    except Post.DoesNotExist:
        return redirect('posts:index')  
    post = Post.objects.get(id=post_id)
    context = {
        'post' : post
    }
    return render(request, 'posts/edit.html', context)

@login_required
def update(request, post_id):

    try:
        post = Post.objects.get(id=post_id, user=request.user)
    except Post.DoesNotExist:
        return redirect('posts:index')
        
    post = Post.objects.get(id=post_id)
    post.body = request.POST['body']
    if len(post.body) < 1 :
        context['error'] = '한 글자 이상은 작성해주세요'
    else:
        if post.body.count('#') < 6:
            post.save()
            return redirect('posts:tagforpost', post_id=post.id)
        else:            
            context['error'] = '태그(#)가 5개를 초과할 수 없습니다'
            body = post.body
            context['body'] = body

    #바로 detail페이지로 가지 않고, tag저장 후 가기 위해서 tagforpost로 이동
    return render(request, 'posts:edit.html', context)    

@login_required
def delete(request, post_id):

    try:    
        post = Post.objects.get(id=post_id, user=request.user)
    except Post.DoesNotExist:
        return redirect('posts:index')

    #post 삭제 시, 연관 tag를 불러오고, 전부 지워버린 후 post를 지움
    post = Post.objects.get(id=post_id)
    tag = post.taginpost.all()
    tag.delete()
    post.delete()

    return redirect('posts:index')

@login_required
def comment_create(request, post_id):
    
    post = Post.objects.get(id=post_id)
    user = request.user
    body = request.POST['body']
    comment = Comment(post=post, user=user, body=body)
    comment.save()

    return redirect('posts:tagforcomment', comment_id=comment.id)

@login_required
def comment_edit(request, comment_id):

    try:    
        comment = Comment.objects.get(id=comment_id, user=request.user)
    except Comment.DoesNotExist:
        return redirect('posts:index')

    comment = Comment.objects.get(id=comment_id)
    post = comment.post
    
    context = {
        'comment' : comment,
        'post' : post
    }
    return render(request, 'posts/comment_edit.html', context)

@login_required
def comment_update(request, comment_id):

    try:    
        comment = Comment.objects.get(id=comment_id, user=request.user)
    except Comment.DoesNotExist:
        return redirect('posts:index')

    comment = Comment.objects.get(id=comment_id)
    post = comment.post
    comment.user = request.user
    comment.body = request.POST['body']
    comment.save()

    #바로 detail페이지로 가지 않고, tag저장 후 가기 위해서 tagforpost로 이동
    return redirect('posts:tagforcomment', comment_id=comment.id)        

@login_required
def comment_delete(request, comment_id):

    try:    
        comment = Comment.objects.get(id=comment_id, user=request.user)
    except Comment.DoesNotExist:
        return redirect('posts:index')
    
    #post 삭제 시, 연관 tag를 불러오고, 전부 지워버린 후 post를 지움
    comment = Comment.objects.get(id=comment_id)
    post = comment.post
    #tag = post.taginpost.all()
    #tag.delete()
    comment.delete()

    return redirect('posts:detail', post_id=post.id)

def tag_filter(request, tag_id):

    tag = Tag.objects.get(id=tag_id)

    return redirect('posts:filter_page', tag_id=tag.id)

@login_required
def tagforcomment(request, comment_id):

    comment = Comment.objects.get(id=comment_id)
    #본문을 str으로 바꾼 뒤, 띄어쓰기대로 Split해서 list로 저장함.    
    body = str(comment.body).split()

    taglist = list()
    original_tags = list()

    #태그가 있는지 확인하는 과정
    if len(body) > 0 :

        for i in body:
            if i == '#':
                pass
            else :
                if i.count('#') > 0:
                    taglist.append(i)
                else:
                    pass

    #글 수정시 태그 중복 저장 방지(새로 작성된 글은 이 과정이 생략됨)
        if comment.tagincomment.all():
            for tag in list(comment.tagincomment.all()):
                original_tags.append(tag)
            if taglist == original_tags:
                return redirect('posts:detail', post_id=post.id)
            else:
                tag = comment.tagincomment.all()
                tag.delete()
        else:
            pass
    #-------------------------------------------------------------             
    #태그가 있을 시, #을 빼내고 문자열로 바꿔주어서 태그에 저장함.
        for i in taglist: 
            x = i.split('#')
            del x[0]
            tag_text = ''.join(x)

            #태그를 스플릿해서 '#'이 빠진 스트링 형태로 tag에 저장함
            tag=Tag(tag=tag_text)
            comment.save()
            "태그"

            #태그가 기존에 있는 태그면, 쿼리셋에 추가만 해주고,
            #태그가 기존에 없는 태그라면 태그를 저장한 뒤에 쿼리셋에 추가함.
            try:
                tag = Tag.objects.get(tag=tag_text)

            except Tag.DoesNotExist:
                tag.save()

            comment.tagincomment.add(tag)

    post=comment.post
    return redirect('posts:detail', post_id=post.id)

@login_required
def like(request, post_id):
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id)

            if request.user in post.liked_users.all():
                post.liked_users.remove(request.user)
            else:
                post.liked_users.add(request.user)

            return redirect('posts:detail', post.id)

        except Post.DoesNotExist:
            pass

    return redirect('posts:index')

@login_required
def filter_page(request, tag_id):
    
    tag = Tag.objects.get(id=tag_id)
    posts = tag.taged_post.all().order_by('-created_at')
    
    #전체 태그에서 가장 많이 쓰인 태그 불러오기    
    # taged_post가 없는 경우 태그 목록에 노출 되지 않도록.
    tags=Tag.objects.exclude(taged_post__isnull=True).annotate(num_posts=Count('taged_post')).order_by('-num_posts')
    tags=list(tags)

    hot_tags = tags[0:9]

    context = {        
        'posts' : posts,
        'hot_tags' : hot_tags,
    }

    return render(request, 'posts/filter_page.html', context )

#성민/my_page의 기초 backbone

def profile_page(request, user_id):



    profile_user = user_id     
    my_posts = list(Post.objects.filter(user = profile_user))
    user = User.objects.get(id=profile_user)

    try:
        user_profile = User_profile.objects.get(user=user)
    except User_profile.DoesNotExist:
        user_profile = User_profile(user=user)
        user_profile.save()

    if user_profile.introduce is None:
        user_introduce = "아직 자기소개가 없습니다."
    else:
        user_introduce = user_profile.introduce

    #팔로우, 팔로우가 없을 경우 에러 방지
    try:
        User_profile.objects.filter(user = profile_user)
        profile = User_profile.objects.get(user = profile_user)
    except User_profile.DoesNotExist:
        profile = None
    #-----------------------------------

    #팔로워 수 뽑아내기
    try:
        count_follower = user.follower.all().count()
    except User.DoesNotExist:
        count_follower = 0
    #-----------------------------------

    #팔로우 수 뽑아내기
    if profile == None:
        count_follow = 0
    else:
        try:        
            count_follow = profile.follow.all().count()
            
        except User_profile.DoesNotExist:
            count_follow = 0
    #-----------------------------------
    #정보수정버튼 노출 관련
    user_id = request.user.id
        
    context = {
            'my_posts' : my_posts,
            'count_follow' : count_follow,
            'count_follower' : count_follower,
            'user_id' : user_id,
            'profile_user' : profile_user,
            'user_introduce' : user_introduce
        }

    return render(request, 'accounts/my_page.html', context)

def post_to_user(request, post_id):


    post  = Post.objects.get(id = post_id)
    user_id = post.user.id

    return redirect('posts:profile_page', user_id=user_id) 